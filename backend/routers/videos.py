import asyncio
import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.db.database import get_db
from backend.auth.dependencies import get_current_user, verify_video_owner
from backend.models.user import User
from backend.services import video_service
from backend.utils.streaming import stream_file_response, validate_file_path
from backend.websocket_manager import manager
from backend.limiter import limiter

router = APIRouter(tags=["videos"])


class DownloadRequest(BaseModel):
    url: str


class VideoUpdateRequest(BaseModel):
    title: str


class VideoOut(BaseModel):
    id: int
    title: str
    source_type: str
    source_url: str | None = None
    status: str
    duration: float | None = None
    file_size: int | None = None
    error_message: str | None = None
    download_progress: float | None = None
    download_speed: float | None = None
    download_eta: int | None = None

    model_config = {"from_attributes": True}


@router.post("/videos/download", response_model=VideoOut)
@limiter.limit("10/hour")
async def download_video(
    request: Request,
    req: DownloadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        video = await video_service.create_download(db, req.url, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    settings = get_settings()
    main_loop = asyncio.get_event_loop()
    background_tasks.add_task(video_service.run_download, video.id, req.url, settings.database_url, main_loop)
    return video


@router.post("/videos/upload", response_model=VideoOut)
@limiter.limit("10/hour")
async def upload_video(
    request: Request,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = get_settings()
    try:
        video = await video_service.create_upload_stream(
            db, file.filename or "video.mp4", file, settings.max_upload_size_bytes, user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except video_service.FileTooLargeError:
        raise HTTPException(status_code=413, detail=f"檔案大小超過上限（{settings.max_upload_size_mb} MB）")
    return video


@router.get("/videos", response_model=list[VideoOut])
async def list_videos(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return await video_service.list_videos(db, limit=limit, offset=offset)
    return await video_service.list_videos(db, owner_id=current_user.id, limit=limit, offset=offset)


@router.get("/videos/{video_id}", response_model=VideoOut)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await verify_video_owner(video_id, db, current_user)
    return video


@router.put("/videos/{video_id}", response_model=VideoOut)
async def update_video(
    video_id: int,
    req: VideoUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await verify_video_owner(video_id, db, current_user)
    if not req.title or not req.title.strip():
        raise HTTPException(status_code=400, detail="標題不可為空")
    video.title = req.title.strip()
    await db.commit()
    await db.refresh(video)
    return video


@router.delete("/videos/{video_id}")
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_video_owner(video_id, db, current_user)
    deleted = await video_service.delete_video(db, video_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="影片不存在")
    return {"detail": "已刪除"}


@router.get("/videos/{video_id}/stream")
async def stream_video(
    video_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await verify_video_owner(video_id, db, current_user)
    if not video.file_path or not os.path.exists(video.file_path):
        raise HTTPException(status_code=404, detail="影片檔案不存在")

    settings = get_settings()
    file_path = video.file_path
    validate_file_path(file_path, settings.upload_dir)
    file_size = os.path.getsize(file_path)
    return stream_file_response(file_path, file_size, request.headers.get("range"))


@router.get("/videos/{video_id}/status", response_model=VideoOut)
async def video_status(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await verify_video_owner(video_id, db, current_user)
    return video


@router.get("/videos/{video_id}/thumbnail")
async def video_thumbnail(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.services.thumbnail_service import generate_thumbnail, get_video_thumbnail_path

    video = await verify_video_owner(video_id, db, current_user)
    if not video.thumbnail_path or not os.path.exists(video.thumbnail_path):
        if video.file_path and os.path.exists(video.file_path):
            thumb_path = get_video_thumbnail_path(video.id)
            if generate_thumbnail(video.file_path, thumb_path):
                video.thumbnail_path = thumb_path
                await db.commit()
    if not video.thumbnail_path or not os.path.exists(video.thumbnail_path):
        raise HTTPException(status_code=404, detail="縮圖不存在")
    return FileResponse(video.thumbnail_path, media_type="image/jpeg")


@router.websocket("/videos/{video_id}/ws/progress")
async def websocket_progress(
    websocket: WebSocket,
    video_id: int,
    token: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket 即時推送影片下載進度"""
    from backend.auth.dependencies import get_current_user_from_token
    if not token:
        await websocket.close(code=4001)
        return

    try:
        current_user = await get_current_user_from_token(token, db)
    except Exception:
        await websocket.close(code=4001)
        return

    await manager.connect(video_id, websocket)
    try:
        while True:
            # 保持連線存活，等待 disconnect
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(video_id, websocket)
