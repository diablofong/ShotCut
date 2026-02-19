"""認證 API 整合測試"""
import pytest


@pytest.mark.asyncio
async def test_login_success(client, admin_user):
    response = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    response = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "wrongpass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post(
        "/api/auth/login",
        data={"username": "nobody", "password": "pass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client, admin_user):
    # 先登入取得 refresh_token cookie
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpass"},
    )
    assert login_resp.status_code == 200
    assert "refresh_token" in login_resp.cookies

    # 使用 refresh_token 換取新 access_token
    refresh_resp = await client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()


@pytest.mark.asyncio
async def test_refresh_without_cookie(client):
    response = await client.post("/api/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(client, admin_user, admin_token):
    # 先登入
    await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpass"},
    )
    # 登出
    resp = await client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_me(client, admin_token):
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
