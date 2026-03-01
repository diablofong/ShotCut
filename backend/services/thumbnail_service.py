import logging
import os
import subprocess

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


def get_video_thumbnail_r2_key(video_id: int) -> str:
    return f"thumbnails/videos/{video_id}.jpg"


def get_highlight_thumbnail_r2_key(highlight_id: int) -> str:
    return f"thumbnails/highlights/{highlight_id}.jpg"


async def upload_thumbnail_to_r2(local_path: str, r2_key: str) -> bool:
    """上傳本地縮圖到 R2，回傳是否成功"""
    from backend.services.storage_service import get_storage_service
    storage = get_storage_service()
    return await storage.upload_file(local_path, r2_key)


