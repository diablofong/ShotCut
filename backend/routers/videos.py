import asyncio
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.db.database import get_db
from backend.auth.dependencies import get_current_user, verify_video_owner
from backend.models.user import User
from backend.services import video_service
from backend.services.storage_service import get_storage_service
from backend.websocket_manager import manager
from backend.limiter import limiter

router = APIRouter(tags=["videos"])


class DownloadRequest(BaseModel):
    url: str


class VideoUpdateRequest(BaseModel):
    title: str


class BatchDeleteRequest(BaseModel):
    ids: list[int]


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


@router.post(
    "/videos/download",
    response_model=VideoOut,
    summary="從 YouTube 下載影片",
    description="提交 YouTube 網址，後台非同步下載。回傳初始 Video 物件（status=pending）。限制每 IP 每小時最多 10 次。",
    responses={
        200: {"description": "已建立下載任務"},
        400: {"description": "非 YouTube 連結"},
        429: {"description": "請求過於頻繁"},
    },
)
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


@router.get(
    "/videos",
    response_model=list[VideoOut],
    summary="影片列表",
    description="回傳目前使用者的所有影片，依建立時間倒序排列。管理員可看到所有使用者的影片。",
    responses={401: {"description": "未登入"}},
)
async def list_videos(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return await video_service.list_videos(db, limit=limit, offset=offset)
    return await video_service.list_videos(db, owner_id=current_user.id, limit=limit, offset=offset)


_ALLOWED_VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
}


@router.get("/videos/upload-url", summary="取得 S3 Presigned PUT 上傳 URL")
@limiter.limit("10/hour")
async def get_upload_url(
    request: Request,
    filename: str = Query(..., description="檔案名稱，如 game.mp4", max_length=255),
    content_type: str = Query(default="video/mp4", description="MIME type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if content_type not in _ALLOWED_VIDEO_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="不支援的 content_type，請使用影片格式")

    from datetime import datetime
    from backend.services.video_service import sanitize_filename
    safe_name = sanitize_filename(filename)
    year = datetime.utcnow().strftime("%Y")
    key = f"videos/{year}/{uuid.uuid4().hex}_{safe_name}"

    storage = get_storage_service()
    upload_url = await storage.generate_presigned_put_url(key, content_type, expires_in=900)

    video = await video_service.create_r2_pending(db, safe_name, key, user_id=current_user.id)
    return {"upload_url": upload_url, "video_id": video.id, "key": key}


@router.get(
    "/videos/{video_id}",
    response_model=VideoOut,
    summary="取得單一影片",
    responses={
        401: {"description": "未登入"},
        403: {"description": "無權存取此影片"},
        404: {"description": "影片不存在"},
    },
)
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


@router.post("/videos/batch/delete")
async def batch_delete_videos(
    req: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not req.ids:
        raise HTTPException(status_code=400, detail="未指定任何 ID")

    if current_user.role != "admin":
        for video_id in req.ids:
            await verify_video_owner(video_id, db, current_user)

    result = await video_service.batch_delete_videos(db, req.ids)
    return {"detail": f"成功刪除 {result['success']} 筆，失敗 {result['failed']} 筆", **result}


@router.post("/videos/{video_id}/confirm", response_model=VideoOut, summary="確認 S3 上傳完成")
@limiter.limit("20/hour")
async def confirm_upload(
    request: Request,
    video_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await verify_video_owner(video_id, db, current_user)
    if video.status != "pending":
        raise HTTPException(status_code=400, detail="影片狀態不正確")
    if not video.r2_key:
        raise HTTPException(status_code=400, detail="此影片無 S3 物件 key")

    # 先原子性地將狀態改為 processing，防止重複 confirm 的競態條件
    video.status = "processing"
    await db.commit()
    await db.refresh(video)

    settings = get_settings()
    background_tasks.add_task(
        video_service.process_r2_upload, video.id, video.r2_key, settings.database_url
    )
    return video


@router.get("/videos/{video_id}/stream")
async def stream_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await verify_video_owner(video_id, db, current_user)
    if not video.r2_key:
        raise HTTPException(status_code=404, detail="影片檔案不存在")
    storage = get_storage_service()
    presigned_url = await storage.generate_presigned_get_url(video.r2_key)
    return RedirectResponse(url=presigned_url, status_code=302)


@router.get("/videos/{video_id}/stream-url")
async def stream_url(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """回傳 presigned GET URL（JSON），供前端 video player 直接使用。
    <video> 元素無法帶 Authorization header，故不能直接用 /stream（302）。
    """
    video = await verify_video_owner(video_id, db, current_user)
    if not video.r2_key:
        raise HTTPException(status_code=404, detail="影片檔案不存在")
    storage = get_storage_service()
    presigned_url = await storage.generate_presigned_get_url(video.r2_key)
    return {"url": presigned_url}


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
    video = await verify_video_owner(video_id, db, current_user)
    if not video.thumbnail_path:
        raise HTTPException(status_code=404, detail="縮圖不存在")
    storage = get_storage_service()
    presigned_url = await storage.generate_presigned_get_url(video.thumbnail_path)
    return RedirectResponse(url=presigned_url, status_code=302)


@router.websocket("/videos/{video_id}/ws/progress")
async def websocket_progress(
    websocket: WebSocket,
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket 即時推送影片下載進度"""
    from backend.auth.dependencies import get_current_user_from_token

    token = websocket.query_params.get("token") or websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=4001)
        return

    try:
        current_user = await get_current_user_from_token(token, db)
    except Exception:
        await websocket.close(code=4001)
        return

    from backend.models.video import Video as VideoModel
    video = await db.get(VideoModel, video_id)
    if not video or (current_user.role != "admin" and video.owner_id != current_user.id):
        await websocket.close(code=4003)
        return

    await manager.connect(video_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(video_id, websocket)
