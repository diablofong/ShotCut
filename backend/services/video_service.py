import asyncio
import os
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.video import Video

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def _is_youtube_url(url: str) -> bool:
    return bool(re.match(r"https?://(www\.)?(youtube\.com|youtu\.be)/", url))


def _video_dir(video_id: int) -> str:
    path = os.path.join(UPLOAD_DIR, str(video_id))
    os.makedirs(path, exist_ok=True)
    return path


async def create_download(db: AsyncSession, url: str, user_id: int | None = None) -> Video:
    if not _is_youtube_url(url):
        raise ValueError("僅支援 YouTube 連結")

    video = Video(title="下載中...", source_type="youtube", source_url=url, status="pending", owner_id=user_id)
    db.add(video)
    await db.commit()
    await db.refresh(video)
    return video


def run_download(video_id: int, url: str, db_url: str):
    """在背景執行的同步下載函式（由 BackgroundTasks 呼叫）"""
    import asyncio
    asyncio.run(_async_download(video_id, url, db_url))


async def _async_download(video_id: int, url: str, db_url: str):
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as AS
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine(db_url)
    session_factory = sessionmaker(engine, class_=AS, expire_on_commit=False)

    async with session_factory() as db:
        video = await db.get(Video, video_id)
        if not video:
            return

        video.status = "downloading"
        video.download_progress = 0.0
        await db.commit()

        output_dir = _video_dir(video_id)
        output_path = os.path.join(output_dir, "original.%(ext)s")

        # 共享進度資料，由 progress_hook（在下載執行緒）寫入
        progress = {"percent": 0.0, "speed": None, "eta": None, "updated": False}
        download_done = False

        def progress_hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded_bytes = d.get("downloaded_bytes", 0)
                progress["percent"] = (downloaded_bytes / total * 100) if total else 0
                progress["speed"] = d.get("speed")
                progress["eta"] = d.get("eta")
                progress["updated"] = True

        async def flush_progress():
            """每 2 秒將進度寫入 DB"""
            while not download_done:
                if progress["updated"]:
                    video.download_progress = round(progress["percent"], 1)
                    video.download_speed = progress["speed"]
                    video.download_eta = int(progress["eta"]) if progress["eta"] else None
                    progress["updated"] = False
                    await db.commit()
                await asyncio.sleep(2)

        try:
            ydl_opts = {
                "format": "best[ext=mp4]/best",
                "outtmpl": output_path,
                "quiet": True,
                "no_warnings": True,
                "js_runtimes": {"node": {}},
                "remote_components": {"ejs:github"},
                "progress_hooks": [progress_hook],
            }

            loop = asyncio.get_event_loop()
            flush_task = asyncio.ensure_future(flush_progress())

            def do_download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=True)

            with ThreadPoolExecutor(max_workers=1) as executor:
                info = await loop.run_in_executor(executor, do_download)

            download_done = True
            await flush_task

            if info is None:
                raise RuntimeError("無法取得影片資訊")

            video.title = info.get("title", "未知標題")
            video.duration = info.get("duration")

            # 找到下載的檔案
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                downloaded = ydl.prepare_filename(info)
            video.file_path = downloaded
            video.file_size = os.path.getsize(downloaded) if os.path.exists(downloaded) else None
            video.status = "completed"
            video.download_progress = 100.0
            video.download_speed = None
            video.download_eta = None

            # 產生縮圖
            from backend.services.thumbnail_service import generate_thumbnail, get_video_thumbnail_path
            thumb_path = get_video_thumbnail_path(video_id)
            if generate_thumbnail(downloaded, thumb_path):
                video.thumbnail_path = thumb_path

        except Exception as e:
            download_done = True
            video.status = "failed"
            video.error_message = str(e)[:2000]

        await db.commit()

    await engine.dispose()


async def create_upload(db: AsyncSession, filename: str, content: bytes, user_id: int | None = None) -> Video:
    allowed_ext = {".mp4", ".avi", ".mov", ".mkv"}
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_ext:
        raise ValueError(f"不支援的檔案格式: {ext}")

    video = Video(title=filename, source_type="upload", status="completed", owner_id=user_id)
    db.add(video)
    await db.commit()
    await db.refresh(video)

    output_dir = _video_dir(video.id)
    file_path = os.path.join(output_dir, f"original{ext}")
    with open(file_path, "wb") as f:
        f.write(content)

    video.file_path = file_path
    video.file_size = len(content)

    # 產生縮圖
    from backend.services.thumbnail_service import generate_thumbnail, get_video_thumbnail_path
    thumb_path = get_video_thumbnail_path(video.id)
    if generate_thumbnail(file_path, thumb_path):
        video.thumbnail_path = thumb_path

    await db.commit()
    await db.refresh(video)
    return video


async def list_videos(db: AsyncSession, owner_id: int | None = None) -> list[Video]:
    stmt = select(Video).order_by(Video.created_at.desc())
    if owner_id is not None:
        stmt = stmt.where(Video.owner_id == owner_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_video(db: AsyncSession, video_id: int) -> Video | None:
    return await db.get(Video, video_id)


async def delete_video(db: AsyncSession, video_id: int) -> bool:
    video = await db.get(Video, video_id)
    if not video:
        return False

    # 刪除檔案
    video_dir = os.path.join(UPLOAD_DIR, str(video_id))
    if os.path.isdir(video_dir):
        shutil.rmtree(video_dir, ignore_errors=True)

    await db.delete(video)
    await db.commit()
    return True
