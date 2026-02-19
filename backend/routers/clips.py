import os
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user, verify_video_owner
from backend.models.user import User
from backend.models.clip import Clip
from backend.services import clip_service
from backend.utils.streaming import stream_file_response, validate_file_path

CLIP_DIR = os.getenv("CLIP_DIR", "./clips")

router = APIRouter(tags=["clips"])

CATEGORY_LABELS = {
    "offense": "進攻",
    "defense": "防守",
    "turnover": "失誤",
    "untagged": "未分類",
}


class ClipOut(BaseModel):
    id: int
    video_id: int
    mark_id: int
    file_path: str | None = None
    duration: float | None = None
    file_size: int | None = None
    status: str
    error_message: str | None = None
    category: str = ""
    label: str = ""
    video_title: str = ""
    player_numbers: list[int] = []
    start_time: float = 0
    end_time: float = 0

    model_config = {"from_attributes": True}


def _clip_to_out(clip: Clip) -> ClipOut:
    mark = clip.mark
    return ClipOut(
        id=clip.id,
        video_id=clip.video_id,
        mark_id=clip.mark_id,
        file_path=clip.file_path,
        duration=clip.duration,
        file_size=clip.file_size,
        status=clip.status,
        error_message=clip.error_message,
        category=mark.category if mark else "",
        label=(mark.label or CATEGORY_LABELS.get(mark.category, mark.category)) if mark else "",
        video_title=clip.video.title if clip.video else "",
        player_numbers=[p.player_number for p in mark.players] if mark else [],
        start_time=mark.start_time if mark else 0,
        end_time=mark.end_time if mark else 0,
    )


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
    # Re-fetch with mark relationships loaded
    loaded = await clip_service.list_clips(db, video_id=video_id)
    return [_clip_to_out(c) for c in loaded]


@router.get("/clips", response_model=list[ClipOut])
async def list_clips(
    video_id: int | None = None,
    category: str | None = None,
    player_number: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if video_id is not None:
        await verify_video_owner(video_id, db, current_user)
    clips = await clip_service.list_clips(
        db, video_id=video_id, category=category, player_number=player_number,
        limit=limit, offset=offset,
    )
    return [_clip_to_out(c) for c in clips]


@router.get("/clips/{clip_id}/stream")
async def stream_clip(
    clip_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clip = await db.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="片段不存在")
    await verify_video_owner(clip.video_id, db, current_user)
    if not clip.file_path or not os.path.exists(clip.file_path):
        raise HTTPException(status_code=404, detail="片段檔案不存在")

    file_path = clip.file_path
    validate_file_path(file_path, CLIP_DIR)
    file_size = os.path.getsize(file_path)
    return stream_file_response(file_path, file_size, request.headers.get("range"))


@router.get("/clips/{clip_id}/download")
async def download_clip(
    clip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clip = await db.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="片段不存在")
    await verify_video_owner(clip.video_id, db, current_user)
    if not clip.file_path or not os.path.exists(clip.file_path):
        raise HTTPException(status_code=404, detail="片段檔案不存在")
    validate_file_path(clip.file_path, CLIP_DIR)
    filename = os.path.basename(clip.file_path)
    encoded = quote(filename)
    return FileResponse(
        clip.file_path, media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )


@router.get("/clips/{clip_id}/thumbnail")
async def clip_thumbnail(
    clip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.services.thumbnail_service import generate_thumbnail, get_clip_thumbnail_path

    clip = await db.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="片段不存在")
    await verify_video_owner(clip.video_id, db, current_user)
    # Lazy 生成
    if not clip.thumbnail_path or not os.path.exists(clip.thumbnail_path):
        if clip.file_path and os.path.exists(clip.file_path):
            thumb_path = get_clip_thumbnail_path(clip.id)
            if generate_thumbnail(clip.file_path, thumb_path, timestamp=0.5):
                clip.thumbnail_path = thumb_path
                await db.commit()
    if not clip.thumbnail_path or not os.path.exists(clip.thumbnail_path):
        raise HTTPException(status_code=404, detail="縮圖不存在")
    return FileResponse(clip.thumbnail_path, media_type="image/jpeg")


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
    return {"detail": "已刪除"}
