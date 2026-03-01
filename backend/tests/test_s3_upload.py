"""S3 Presigned PUT 上傳流程 + filetype 二次驗證測試"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models.video import Video


@pytest.mark.asyncio
async def test_get_upload_url_success(client, user_token, mock_storage):
    """取得 Presigned PUT URL 成功"""
    response = await client.get(
        "/api/videos/upload-url?filename=game.mp4&content_type=video/mp4",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "upload_url" in data
    assert "video_id" in data
    assert "key" in data
    assert data["upload_url"].startswith("https://mock-s3")


@pytest.mark.asyncio
async def test_get_upload_url_invalid_content_type(client, user_token, mock_storage):
    """不允許的 content_type 應回傳 400"""
    response = await client.get(
        "/api/videos/upload-url?filename=evil.exe&content_type=application/octet-stream",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_upload_url_unauthenticated(client):
    """未認證不能取得上傳 URL"""
    response = await client.get("/api/videos/upload-url?filename=game.mp4")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_stream_video_returns_302(client, user_token, r2_video, mock_storage):
    """串流影片應回傳 302 redirect 至 presigned GET URL"""
    response = await client.get(
        f"/api/videos/{r2_video.id}/stream",
        headers={"Authorization": f"Bearer {user_token}"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "mock-s3" in response.headers["location"]


@pytest.mark.asyncio
async def test_stream_video_no_r2_key(client, user_token, sample_video, mock_storage):
    """無 r2_key 的影片無法串流（404）"""
    response = await client.get(
        f"/api/videos/{sample_video.id}/stream",
        headers={"Authorization": f"Bearer {user_token}"},
        follow_redirects=False,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_thumbnail_returns_302(client, user_token, r2_video, mock_storage):
    """縮圖端點應回傳 302 redirect"""
    response = await client.get(
        f"/api/videos/{r2_video.id}/thumbnail",
        headers={"Authorization": f"Bearer {user_token}"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "mock-s3" in response.headers["location"]


@pytest.mark.asyncio
async def test_confirm_upload_pending_video(client, user_token, db_session, regular_user, mock_storage):
    """confirm 端點：pending 影片成功觸發背景處理"""
    video = Video(
        title="待確認影片",
        source_type="upload",
        status="pending",
        r2_key="videos/2026/test_pending.mp4",
        owner_id=regular_user.id,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    with patch("backend.routers.videos.video_service.process_r2_upload") as mock_task:
        response = await client.post(
            f"/api/videos/{video.id}/confirm",
            headers={"Authorization": f"Bearer {user_token}"},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "processing"  # I5：confirm 後立即設為 processing 防競態


@pytest.mark.asyncio
async def test_confirm_upload_wrong_status(client, user_token, r2_video, mock_storage):
    """非 pending 狀態的影片 confirm 應回傳 400"""
    response = await client.post(
        f"/api/videos/{r2_video.id}/confirm",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400


def test_filetype_validation_invalid_file():
    """filetype 二次驗證：EXE magic bytes 不應通過影片格式檢查"""
    import filetype as ft

    # EXE magic bytes（MZ header）
    exe_bytes = b"MZ" + b"\x00" * 260
    kind = ft.match(exe_bytes)
    assert kind is None or not kind.mime.startswith("video/"), "EXE magic bytes 不應被識別為影片"


def test_filetype_validation_pdf_file():
    """filetype 二次驗證：PDF magic bytes 不應通過影片格式檢查"""
    import filetype as ft

    # PDF magic bytes
    pdf_bytes = b"%PDF-1.4" + b"\x00" * 254
    kind = ft.match(pdf_bytes)
    assert kind is None or not kind.mime.startswith("video/"), "PDF magic bytes 不應被識別為影片"


@pytest.mark.asyncio
async def test_filetype_validation_valid_video():
    """filetype 二次驗證：MP4 magic bytes 應通過驗證"""
    import filetype as ft

    # MP4 magic bytes（ftyp box）
    mp4_header = (
        b"\x00\x00\x00\x1c"  # box size
        b"ftyp"              # box type
        b"mp42"              # major brand
        b"\x00\x00\x00\x00"  # minor version
        b"mp42mp41"          # compatible brands
        + b"\x00" * 240
    )
    kind = ft.match(mp4_header)
    assert kind is not None and kind.mime.startswith("video/"), "MP4 magic bytes 應被識別為影片"
