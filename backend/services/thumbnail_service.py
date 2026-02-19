import logging
import os
import subprocess

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings

logger = logging.getLogger(__name__)


def generate_thumbnail(
    video_path: str,
    output_path: str,
    timestamp: float = 1.0,
) -> bool:
    """從影片的指定時間點擷取一幀作為縮圖，回傳是否成功"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-vf", "scale=320:-1",
                output_path,
            ],
            capture_output=True,
            check=True,
            timeout=60,
        )
        return os.path.exists(output_path)
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg 縮圖生成超時 [%s]", video_path)
        return False
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="replace") if e.stderr else "unknown"
        logger.error("FFmpeg 縮圖生成失敗 [%s]: %s", video_path, stderr[:500])
        return False
    except Exception as e:
        logger.error("縮圖生成異常 [%s]: %s", video_path, str(e))
        return False


def get_video_thumbnail_path(video_id: int) -> str:
    thumbnail_dir = get_settings().thumbnail_dir
    return os.path.join(thumbnail_dir, "videos", f"{video_id}.jpg")


def get_clip_thumbnail_path(clip_id: int) -> str:
    thumbnail_dir = get_settings().thumbnail_dir
    return os.path.join(thumbnail_dir, "clips", f"{clip_id}.jpg")


def get_highlight_thumbnail_path(highlight_id: int) -> str:
    thumbnail_dir = get_settings().thumbnail_dir
    return os.path.join(thumbnail_dir, "highlights", f"{highlight_id}.jpg")


def _needs_thumbnail(thumbnail_path: str | None) -> bool:
    """檢查是否需要生成縮圖（路徑為空或檔案不存在）"""
    return not thumbnail_path or not os.path.exists(thumbnail_path)


async def regenerate_missing_thumbnails(db: AsyncSession) -> None:
    """補生成所有缺少縮圖的影片/片段/精華（包含路徑存在但檔案遺失的情況）"""
    from backend.models.video import Video
    from backend.models.clip import Clip
    from backend.models.highlight import Highlight

    count = 0

    # 影片
    result = await db.execute(
        select(Video).where(
            Video.file_path.isnot(None),
            Video.status == "completed",
        )
    )
    for video in result.scalars().all():
        if not _needs_thumbnail(video.thumbnail_path):
            continue
        if not video.file_path or not os.path.exists(video.file_path):
            continue
        thumb_path = get_video_thumbnail_path(video.id)
        if generate_thumbnail(video.file_path, thumb_path):
            video.thumbnail_path = thumb_path
            count += 1
            logger.info("補生成影片縮圖: id=%d", video.id)

    # 片段
    result = await db.execute(
        select(Clip).where(
            Clip.file_path.isnot(None),
            Clip.status == "completed",
        )
    )
    for clip in result.scalars().all():
        if not _needs_thumbnail(clip.thumbnail_path):
            continue
        if not clip.file_path or not os.path.exists(clip.file_path):
            continue
        thumb_path = get_clip_thumbnail_path(clip.id)
        if generate_thumbnail(clip.file_path, thumb_path, timestamp=0.5):
            clip.thumbnail_path = thumb_path
            count += 1
            logger.info("補生成片段縮圖: id=%d", clip.id)

    # 精華
    result = await db.execute(
        select(Highlight).where(
            Highlight.file_path.isnot(None),
            Highlight.status == "completed",
        )
    )
    for hl in result.scalars().all():
        if not _needs_thumbnail(hl.thumbnail_path):
            continue
        if not hl.file_path or not os.path.exists(hl.file_path):
            continue
        thumb_path = get_highlight_thumbnail_path(hl.id)
        if generate_thumbnail(hl.file_path, thumb_path):
            hl.thumbnail_path = thumb_path
            count += 1
            logger.info("補生成精華縮圖: id=%d", hl.id)

    await db.commit()
    if count > 0:
        logger.info("縮圖補生成完成，共處理 %d 筆", count)
    else:
        logger.info("所有縮圖皆已存在，無需補生成")
