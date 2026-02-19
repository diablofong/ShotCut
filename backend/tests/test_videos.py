"""影片 API 整合測試"""
import pytest


@pytest.mark.asyncio
async def test_list_videos_authenticated(client, user_token, sample_video):
    response = await client.get(
        "/api/videos",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_videos_unauthenticated(client):
    response = await client.get("/api/videos")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_video_owner(client, user_token, sample_video):
    response = await client.get(
        f"/api/videos/{sample_video.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == sample_video.id


@pytest.mark.asyncio
async def test_get_video_other_user_forbidden(client, other_token, sample_video):
    """非擁有者不可存取影片"""
    response = await client.get(
        f"/api/videos/{sample_video.id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_see_all_videos(client, admin_token, sample_video):
    """管理員可以看到所有影片"""
    response = await client.get(
        "/api/videos",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_delete_video_owner(client, db_session, user_token, sample_video):
    response = await client.delete(
        f"/api/videos/{sample_video.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_video_other_user_forbidden(client, other_token, sample_video):
    response = await client.delete(
        f"/api/videos/{sample_video.id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403
