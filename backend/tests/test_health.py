"""健康檢查端點測試"""
import pytest


@pytest.mark.asyncio
async def test_health_no_auth(client):
    """/api/health 不需要認證"""
    response = await client.get("/api/health")
    assert response.status_code in (200, 503)  # 依 DB 連線狀態
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_returns_healthy(client):
    """測試環境 DB 可用，應回傳 healthy"""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "ok"
