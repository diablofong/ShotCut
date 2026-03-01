import asyncio
import os
import re
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

            progress = {"percent": 0.0, "speed": None, "eta": None, "updated": False}
            download_done = False

            def _broadcast(data: dict):
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

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    downloaded = ydl.prepare_filename(info)

                # 上傳至 S3
                from backend.services.storage_service import get_storage_service
                from datetime import datetime
                import uuid as _uuid
                storage = get_storage_service()
                year = datetime.utcnow().strftime("%Y")
                s3_key = f"videos/{year}/{_uuid.uuid4().hex}_{os.path.basename(downloaded)}"
                file_size = os.path.getsize(downloaded) if os.path.exists(downloaded) else None
                await storage.upload_file(downloaded, s3_key)  # upload_file 會刪除本地暫存

                video.r2_key = s3_key
                video.file_size = file_size
                video.status = "completed"
                video.download_progress = 100.0
                video.download_speed = None
                video.download_eta = None

                # 產生縮圖（從 S3 下載暫存 → FFmpeg → 上傳縮圖）
                import tempfile
                from backend.services.thumbnail_service import generate_thumbnail, get_video_thumbnail_r2_key
                thumb_key = get_video_thumbnail_r2_key(video_id)
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_v:
                    tmp_video_path = tmp_v.name
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_t:
                    tmp_thumb_path = tmp_t.name
                try:
                    presigned_get = await storage.generate_presigned_get_url(s3_key, expires_in=300)
                    import httpx
                    async with httpx.AsyncClient() as client:
                        async with client.stream("GET", presigned_get) as response:
                            response.raise_for_status()
                            with open(tmp_video_path, "wb") as f:
                                async for chunk in response.aiter_bytes():
                                    f.write(chunk)
                    if generate_thumbnail(tmp_video_path, tmp_thumb_path):
                        await storage.upload_file(tmp_thumb_path, thumb_key)
                        video.thumbnail_path = thumb_key
                except Exception:
                    pass
                finally:
                    for p in (tmp_video_path, tmp_thumb_path):
                        if os.path.exists(p):
                            os.remove(p)

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
    filename = os.path.basename(filename)
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    if not filename:
        filename = 'video.mp4'
    return filename


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

    from backend.services.storage_service import get_storage_service
    storage = get_storage_service()
    if video.r2_key:
        await storage.delete_object(video.r2_key)
    if video.thumbnail_path:
        await storage.delete_object(video.thumbnail_path)

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
    import filetype as ft
    import httpx
    import tempfile
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as AS
    from sqlalchemy.orm import sessionmaker
    from backend.services.storage_service import get_storage_service
    from backend.services.thumbnail_service import generate_thumbnail, get_video_thumbnail_r2_key
    from backend.config import get_settings

    settings = get_settings()
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AS, expire_on_commit=False)

    async with async_session() as db:
        try:
            video = await db.get(Video, video_id)
            if not video:
                return

            storage = get_storage_service()
            # 後端 httpx 使用 internal=True，避免 localhost:9000 在容器內無法解析
            presigned_get = await storage.generate_presigned_get_url(r2_key, expires_in=300, internal=True)

            # 1. 檢查檔案大小（HEAD request）
            async with httpx.AsyncClient() as client:
                head_resp = await client.head(presigned_get)
                content_length = int(head_resp.headers.get("content-length", 0))

            if content_length > settings.max_upload_size_bytes:
                await storage.delete_object(r2_key)
                video.status = "failed"
                video.error_message = f"檔案超過大小限制（{settings.max_upload_size_mb}MB）"
                await db.commit()
                return

            # 2. 下載前 262 bytes 進行 filetype 二次驗證（internal URL 供容器內 httpx 使用）
            async with httpx.AsyncClient() as client:
                range_resp = await client.get(presigned_get, headers={"Range": "bytes=0-261"})
                header_bytes = await range_resp.aread()

            kind = ft.match(header_bytes)
            if kind is None or not kind.mime.startswith("video/"):
                await storage.delete_object(r2_key)
                video.status = "failed"
                video.error_message = "檔案格式驗證失敗（非影片格式）"
                await db.commit()
                return

            # 3. 驗證通過：更新狀態並觸發縮圖生成
            video.status = "completed"
            if content_length:
                video.file_size = content_length
            await db.commit()

            thumb_key = get_video_thumbnail_r2_key(video_id)
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_thumb:
                tmp_thumb_path = tmp_thumb.name

            try:
                # 直接將 presigned URL 傳給 FFmpeg（internal=True，容器內可存取）
                ffmpeg_presigned = await storage.generate_presigned_get_url(r2_key, expires_in=600, internal=True)
                success = generate_thumbnail(ffmpeg_presigned, tmp_thumb_path)
                if success:
                    await storage.upload_file(tmp_thumb_path, thumb_key)
                    video = await db.get(Video, video_id)
                    if video:
                        video.thumbnail_path = thumb_key
                        await db.commit()
            except Exception:
                pass
            finally:
                if os.path.exists(tmp_thumb_path):
                    os.remove(tmp_thumb_path)
        except Exception as e:
            video = await db.get(Video, video_id)
            if video:
                video.status = "failed"
                video.error_message = str(e)[:2000]
                await db.commit()
        finally:
            await engine.dispose()


async def batch_delete_videos(db: AsyncSession, video_ids: list[int]) -> dict[str, int]:
    """批量刪除影片，回傳成功與失敗數量"""
    success = 0
    failed = 0

    from backend.services.storage_service import get_storage_service
    storage = get_storage_service()

    for video_id in video_ids:
        video = await db.get(Video, video_id)
        if not video:
            failed += 1
            continue

        if video.r2_key:
            await storage.delete_object(video.r2_key)
        if video.thumbnail_path:
            await storage.delete_object(video.thumbnail_path)

        await db.delete(video)
        success += 1

    await db.commit()
    return {"success": success, "failed": failed}
