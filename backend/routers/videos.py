import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user, verify_video_owner
from backend.models.user import User
from backend.services import video_service

router = APIRouter(tags=["videos"])


class DownloadRequest(BaseModel):
    url: str


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

    model_config = {"from_attributes": True}


@router.post("/videos/download", response_model=VideoOut)
async def download_video(
    req: DownloadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        video = await video_service.create_download(db, req.url, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db_url = os.getenv("DATABASE_URL", "mysql+asyncmy://shotcut:shotcut_pass@localhost:3306/shotcut")
    background_tasks.add_task(video_service.run_download, video.id, req.url, db_url)
    return video


@router.post("/videos/upload", response_model=VideoOut)
async def upload_video(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    try:
        video = await video_service.create_upload(db, file.filename or "video.mp4", content, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return video


@router.get("/videos", response_model=list[VideoOut])
async def list_videos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return await video_service.list_videos(db)
    return await video_service.list_videos(db, owner_id=current_user.id)


@router.get("/videos/{video_id}", response_model=VideoOut)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await verify_video_owner(video_id, db, current_user)
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
    return {"ok": True}


@router.get("/videos/{video_id}/status", response_model=VideoOut)
async def video_status(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await verify_video_owner(video_id, db, current_user)
    return video
