"""GET /api/config 端點與 Security Headers 測試"""
import pytest


@pytest.mark.asyncio
async def test_config_returns_features(client):
    """GET /api/config 應回傳 features 物件"""
    response = await client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert "clips" in data["features"]
    assert "highlights" in data["features"]
    assert "sharing" in data["features"]


@pytest.mark.asyncio
async def test_config_no_credentials(client):
    """GET /api/config 不應洩漏 S3 credentials"""
    response = await client.get("/api/config")
    data = response.json()
    text = str(data).lower()
    for secret_word in ["access_key", "secret_key", "endpoint", "bucket", "password"]:
        assert secret_word not in text, f"config 回應不應包含 '{secret_word}'"


@pytest.mark.asyncio
async def test_config_no_auth_required(client):
    """GET /api/config 不需要認證"""
    response = await client.get("/api/config")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_security_headers_on_api(client):
    """所有 API 回應應包含安全標頭"""
    response = await client.get("/api/config")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert "strict-origin-when-cross-origin" in response.headers.get("referrer-policy", "")


@pytest.mark.asyncio
async def test_security_headers_on_auth_endpoint(client):
    """認證端點也應有安全標頭"""
    response = await client.post("/api/auth/login", json={"username": "x", "password": "x"})
    assert response.headers.get("x-content-type-options") == "nosniff"
