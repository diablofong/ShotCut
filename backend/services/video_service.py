import asyncio
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor

import filetype
import yt_dlp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import UploadFile

from backend.config import get_settings
from backend.models.video import Video


class FileTooLargeError(Exception):
    pass


def _is_youtube_url(url: str) -> bool:
    return bool(re.match(r"https?://(www\.)?(youtube\.com|youtu\.be)/", url))


def _video_dir(video_id: int) -> str:
    upload_dir = get_settings().upload_dir
    path = os.path.join(upload_dir, str(video_id))
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


def run_download(video_id: int, url: str, db_url: str, main_loop: asyncio.AbstractEventLoop | None = None):
    """在背景執行的同步下載函式（由 BackgroundTasks 呼叫）"""
    asyncio.run(_async_download(video_id, url, db_url, main_loop))


async def _async_download(video_id: int, url: str, db_url: str, main_loop: asyncio.AbstractEventLoop | None = None):
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as AS
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine(db_url)
    try:
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

            def _broadcast(data: dict):
                """跨事件迴圈廣播至 WebSocket 用戶端"""
                if main_loop and main_loop.is_running():
                    from backend.websocket_manager import manager as ws_manager
                    asyncio.run_coroutine_threadsafe(ws_manager.broadcast(video_id, data), main_loop)

            def progress_hook(d):
                if d["status"] == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    downloaded_bytes = d.get("downloaded_bytes", 0)
                    progress["percent"] = (downloaded_bytes / total * 100) if total else 0
                    progress["speed"] = d.get("speed")
                    progress["eta"] = d.get("eta")
                    progress["updated"] = True

            async def flush_progress():
                """每 2 秒將進度寫入 DB 並廣播至 WebSocket"""
                while not download_done:
                    if progress["updated"]:
                        pct = round(progress["percent"], 1)
                        spd = progress["speed"]
                        eta = int(progress["eta"]) if progress["eta"] else None
                        video.download_progress = pct
                        video.download_speed = spd
                        video.download_eta = eta
                        progress["updated"] = False
                        await db.commit()
                        _broadcast({
                            "status": "downloading",
                            "progress": pct,
                            "speed": str(round(spd, 0)) if spd else None,
                            "eta": eta,
                        })
                    await asyncio.sleep(2)

            try:
                ydl_opts = {
                    "format": "best[ext=mp4]/best",
                    "outtmpl": output_path,
                    "quiet": True,
                    "no_warnings": True,
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

                _broadcast({"status": "completed", "progress": 100.0})

            except Exception as e:
                download_done = True
                video.status = "failed"
                video.error_message = str(e)[:2000]
                _broadcast({"status": "failed"})

            await db.commit()
    finally:
        await engine.dispose()


def sanitize_filename(filename: str) -> str:
    """清理檔案名稱，移除路徑遍歷字符"""
    # 移除路徑分隔符和特殊字符
    filename = os.path.basename(filename)
    # 移除 .. 和其他危險字符
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    # 如果清理後為空，使用預設名稱
    if not filename:
        filename = 'video.mp4'
    return filename


async def create_upload_stream(
    db: AsyncSession, filename: str, file: UploadFile, max_size: int, user_id: int | None = None
) -> Video:
    # 允許的影片 MIME 類型
    ALLOWED_VIDEO_MIMES = {
        'video/mp4',
        'video/quicktime',  # .mov
        'video/x-msvideo',  # .avi
        'video/x-matroska',  # .mkv
    }

    allowed_ext = {".mp4", ".avi", ".mov", ".mkv"}

    # 清理檔案名稱
    filename = sanitize_filename(filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_ext:
        raise ValueError(f"不支援的檔案格式: {ext}")

    # 讀取前 262 bytes 進行魔數檢查
    first_chunk = await file.read(262)
    if not first_chunk:
        raise ValueError("檔案為空")

    kind = filetype.guess(first_chunk)
    if not kind or kind.mime not in ALLOWED_VIDEO_MIMES:
        detected_type = kind.mime if kind else 'unknown'
        raise ValueError(f"檔案類型不符，偵測到: {detected_type}，需要影片檔案")

    # 重置檔案指針以繼續讀取
    await file.seek(0)

    video = Video(title=filename, source_type="upload", status="completed", owner_id=user_id)
    db.add(video)
    await db.commit()
    await db.refresh(video)

    output_dir = _video_dir(video.id)
    file_path = os.path.join(output_dir, f"original{ext}")
    total_written = 0
    try:
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                total_written += len(chunk)
                if total_written > max_size:
                    raise FileTooLargeError()
                f.write(chunk)
    except FileTooLargeError:
        if os.path.exists(file_path):
            os.remove(file_path)
        await db.delete(video)
        await db.commit()
        raise

    video.file_path = file_path
    video.file_size = total_written

    # 讀取影片時長
    try:
        import ffmpeg
        probe = ffmpeg.probe(file_path)
        video.duration = float(probe['format']['duration'])
    except Exception:
        # 如果讀取失敗，設為 None
        video.duration = None

    await db.commit()
    await db.refresh(video)

    # 背景生成縮圖（不阻塞回應）
    import asyncio
    from backend.services.thumbnail_service import generate_thumbnail, get_video_thumbnail_path

    async def generate_thumbnail_async():
        """背景任務：生成縮圖並透過 WebSocket 通知"""
        thumb_path = get_video_thumbnail_path(video.id)
        success = generate_thumbnail(file_path, thumb_path)

        if success:
            # 更新資料庫
            from backend.database import get_async_engine
            from sqlalchemy.ext.asyncio import AsyncSession
            engine = get_async_engine()
            async with AsyncSession(engine) as session:
                vid = await session.get(Video, video.id)
                if vid:
                    vid.thumbnail_path = thumb_path
                    await session.commit()
            await engine.dispose()

        # 透過 WebSocket 推送縮圖生成完成事件
        from backend.websocket_manager import manager
        await manager.broadcast(video.id, {
            "event": "thumbnail_generated",
            "success": success,
            "video_id": video.id,
        })

    asyncio.create_task(generate_thumbnail_async())

    return video


async def list_videos(
    db: AsyncSession, owner_id: int | None = None, limit: int = 100, offset: int = 0
) -> list[Video]:
    stmt = select(Video).order_by(Video.created_at.desc())
    if owner_id is not None:
        stmt = stmt.where(Video.owner_id == owner_id)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_video(db: AsyncSession, video_id: int) -> Video | None:
    return await db.get(Video, video_id)


async def delete_video(db: AsyncSession, video_id: int) -> bool:
    video = await db.get(Video, video_id)
    if not video:
        return False

    upload_dir = get_settings().upload_dir
    video_dir = os.path.join(upload_dir, str(video_id))
    if os.path.isdir(video_dir):
        shutil.rmtree(video_dir, ignore_errors=True)

    # 刪除縮圖
    from backend.services.thumbnail_service import get_video_thumbnail_path
    thumbnail_path = get_video_thumbnail_path(video_id)
    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)

    await db.delete(video)
    await db.commit()
    return True


async def create_r2_pending(db: AsyncSession, filename: str, r2_key: str, user_id: int | None = None) -> Video:
    title = os.path.splitext(filename)[0]
    video = Video(title=title, source_type="upload", status="pending", r2_key=r2_key, owner_id=user_id)
    db.add(video)
    await db.commit()
    await db.refresh(video)
    return video


def process_r2_upload(video_id: int, r2_key: str, db_url: str) -> None:
    asyncio.run(_async_process_r2_upload(video_id, r2_key, db_url))


async def _async_process_r2_upload(video_id: int, r2_key: str, db_url: str) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as AS
    from sqlalchemy.orm import sessionmaker
    from backend.services.storage_service import get_storage_service

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AS, expire_on_commit=False)

    async with async_session() as db:
        try:
            video = await db.get(Video, video_id)
            if not video:
                return
            video.status = "completed"
            await db.commit()

            storage = get_storage_service()
            import tempfile

            from backend.services.thumbnail_service import generate_thumbnail, get_video_thumbnail_r2_key
            thumb_key = get_video_thumbnail_r2_key(video_id)
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_video:
                tmp_video_path = tmp_video.name
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_thumb:
                tmp_thumb_path = tmp_thumb.name

            try:
                presigned_get = await storage.generate_presigned_get_url(r2_key, expires_in=300)
                import httpx
                async with httpx.AsyncClient() as client:
                    async with client.stream("GET", presigned_get) as response:
                        response.raise_for_status()
                        with open(tmp_video_path, "wb") as f:
                            async for chunk in response.aiter_bytes():
                                f.write(chunk)

                success = generate_thumbnail(tmp_video_path, tmp_thumb_path)
                if success:
                    await storage.upload_file(tmp_thumb_path, thumb_key)
                    video = await db.get(Video, video_id)
                    if video:
                        video.thumbnail_path = thumb_key
                        await db.commit()
            except Exception:
                pass
            finally:
                for p in (tmp_video_path, tmp_thumb_path):
                    if os.path.exists(p):
                        os.remove(p)
        except Exception:
            video = await db.get(Video, video_id)
            if video:
                video.status = "failed"
                await db.commit()
        finally:
            await engine.dispose()


async def batch_delete_videos(db: AsyncSession, video_ids: list[int]) -> dict[str, int]:
    """批量刪除影片，回傳成功與失敗數量"""
    success = 0
    failed = 0
    upload_dir = get_settings().upload_dir
    from backend.services.thumbnail_service import get_video_thumbnail_path

    for video_id in video_ids:
        video = await db.get(Video, video_id)
        if not video:
            failed += 1
            continue

        video_dir = os.path.join(upload_dir, str(video_id))
        if os.path.isdir(video_dir):
            shutil.rmtree(video_dir, ignore_errors=True)

        # 刪除縮圖
        thumbnail_path = get_video_thumbnail_path(video_id)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

        await db.delete(video)
        success += 1

    await db.commit()
    return {"success": success, "failed": failed}
