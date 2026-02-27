"""Feature Flag 整合測試：ENABLE_CLIPS / ENABLE_HIGHLIGHTS / ENABLE_SHARING"""
import pytest

from backend.config import get_settings


@pytest.mark.asyncio
async def test_clips_disabled_returns_404(client, user_token, monkeypatch):
    """ENABLE_CLIPS=false 時，所有 /clips 端點應回傳 404"""
    monkeypatch.setenv("ENABLE_CLIPS", "false")
    get_settings.cache_clear()
    try:
        response = await client.get(
            "/api/clips",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 404
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_clips_enabled_by_default(client, user_token):
    """預設情況下 /clips 應正常存取（200）"""
    get_settings.cache_clear()
    response = await client.get(
        "/api/clips",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_highlights_disabled_returns_404(client, user_token, monkeypatch):
    """ENABLE_HIGHLIGHTS=false 時，所有 /highlights 端點應回傳 404"""
    monkeypatch.setenv("ENABLE_HIGHLIGHTS", "false")
    get_settings.cache_clear()
    try:
        response = await client.get(
            "/api/highlights",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 404
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_highlights_enabled_by_default(client, user_token):
    """預設情況下 /highlights 應正常存取（200）"""
    get_settings.cache_clear()
    response = await client.get(
        "/api/highlights",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_sharing_disabled_returns_404(client, monkeypatch):
    """ENABLE_SHARING=false 時，/shares/{token} 公開端點應回傳 404"""
    monkeypatch.setenv("ENABLE_SHARING", "false")
    get_settings.cache_clear()
    try:
        response = await client.get("/api/shares/some-token")
        assert response.status_code == 404
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_sharing_enabled_by_default(client):
    """預設情況下 /shares/{token} 存取不存在的 token 應回傳 404（not found），不是功能未啟用"""
    get_settings.cache_clear()
    response = await client.get("/api/shares/nonexistent-token")
    assert response.status_code == 404
    assert response.json()["detail"] != "此功能未啟用"
