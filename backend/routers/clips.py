from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user, verify_video_owner
from backend.models.user import User
from backend.models.clip import Clip
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
async def extract_clips(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_video_owner(video_id, db, current_user)
    try:
        clips = await clip_service.extract_all_clips(db, video_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return clips


@router.get("/clips", response_model=list[ClipOut])
async def list_clips(
    video_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if video_id is not None:
        await verify_video_owner(video_id, db, current_user)
    return await clip_service.list_clips(db, video_id)


@router.delete("/clips/{clip_id}")
async def delete_clip(
    clip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clip = await db.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="片段不存在")

    await verify_video_owner(clip.video_id, db, current_user)

    deleted = await clip_service.delete_clip(db, clip_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="片段不存在")
    return {"ok": True}
