import os
import subprocess

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.clip import Clip
from backend.models.mark import Mark
from backend.models.video import Video

CLIP_DIR = os.getenv("CLIP_DIR", "./clips")


async def extract_clip(db: AsyncSession, mark: Mark, video: Video) -> Clip:
    """從影片切割單一標記對應的片段"""
    clip = Clip(
        video_id=video.id,
        mark_id=mark.id,
        status="processing",
    )
    db.add(clip)
    await db.commit()
    await db.refresh(clip)

    output_dir = os.path.join(CLIP_DIR, str(video.id))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{mark.id}.mp4")

    try:
        duration = mark.end_time - mark.start_time
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", str(mark.start_time),
                "-i", video.file_path,
                "-t", str(duration),
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                output_path,
            ],
            capture_output=True,
            check=True,
        )
        clip.file_path = output_path
        clip.duration = duration
        clip.file_size = os.path.getsize(output_path)
        clip.status = "completed"
    except subprocess.CalledProcessError as e:
        clip.status = "failed"
        clip.error_message = e.stderr.decode()[:2000] if e.stderr else "FFmpeg 錯誤"

    await db.commit()
    await db.refresh(clip)
    return clip


async def extract_all_clips(db: AsyncSession, video_id: int) -> list[Clip]:
    """批次擷取影片所有標記的片段"""
    video = await db.get(Video, video_id)
    if not video or video.status != "completed" or not video.file_path:
        raise ValueError("影片不存在或尚未完成")

    result = await db.execute(select(Mark).where(Mark.video_id == video_id))
    marks = list(result.scalars().all())

    clips = []
    for mark in marks:
        clip = await extract_clip(db, mark, video)
        clips.append(clip)
    return clips


async def list_clips(db: AsyncSession, video_id: int | None = None) -> list[Clip]:
    stmt = select(Clip)
    if video_id:
        stmt = stmt.where(Clip.video_id == video_id)
    stmt = stmt.order_by(Clip.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_clip(db: AsyncSession, clip_id: int) -> bool:
    clip = await db.get(Clip, clip_id)
    if not clip:
        return False
    if clip.file_path and os.path.exists(clip.file_path):
        os.remove(clip.file_path)
    await db.delete(clip)
    await db.commit()
    return True
