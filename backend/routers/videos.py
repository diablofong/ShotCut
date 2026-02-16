import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
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
):
    try:
        video = await video_service.create_download(db, req.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db_url = os.getenv("DATABASE_URL", "mysql+asyncmy://shotcut:shotcut_pass@localhost:3306/shotcut")
    background_tasks.add_task(video_service.run_download, video.id, req.url, db_url)
    return video


@router.post("/videos/upload", response_model=VideoOut)
async def upload_video(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    try:
        video = await video_service.create_upload(db, file.filename or "video.mp4", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return video


@router.get("/videos", response_model=list[VideoOut])
async def list_videos(db: AsyncSession = Depends(get_db)):
    return await video_service.list_videos(db)


@router.get("/videos/{video_id}", response_model=VideoOut)
async def get_video(video_id: int, db: AsyncSession = Depends(get_db)):
    video = await video_service.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="影片不存在")
    return video


@router.delete("/videos/{video_id}")
async def delete_video(video_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await video_service.delete_video(db, video_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="影片不存在")
    return {"ok": True}


@router.get("/videos/{video_id}/status", response_model=VideoOut)
async def video_status(video_id: int, db: AsyncSession = Depends(get_db)):
    video = await video_service.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="影片不存在")
    return video
