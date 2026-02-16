from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.services import clip_service

router = APIRouter(tags=["clips"])


class ClipOut(BaseModel):
    id: int
    video_id: int
    mark_id: int
    file_path: str | None = None
    duration: float | None = None
    file_size: int | None = None
    status: str
    error_message: str | None = None

    model_config = {"from_attributes": True}


@router.post("/videos/{video_id}/clips", response_model=list[ClipOut])
async def extract_clips(video_id: int, db: AsyncSession = Depends(get_db)):
    try:
        clips = await clip_service.extract_all_clips(db, video_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return clips


@router.get("/clips", response_model=list[ClipOut])
async def list_clips(video_id: int | None = None, db: AsyncSession = Depends(get_db)):
    return await clip_service.list_clips(db, video_id)


@router.delete("/clips/{clip_id}")
async def delete_clip(clip_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await clip_service.delete_clip(db, clip_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="片段不存在")
    return {"ok": True}
