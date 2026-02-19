"""標記 API 整合測試"""
import pytest
from backend.models.mark import Mark


@pytest.mark.asyncio
async def test_create_mark(client, user_token, sample_video):
    response = await client.post(
        f"/api/videos/{sample_video.id}/marks",
        json={
            "start_time": 10.0,
            "end_time": 20.0,
            "category": "offense",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == sample_video.id
    assert data["category"] == "offense"


@pytest.mark.asyncio
async def test_list_marks(client, user_token, db_session, sample_video):
    # 先建立一個標記
    mark = Mark(
        video_id=sample_video.id,
        start_time=5.0,
        end_time=15.0,
        category="defense",
    )
    db_session.add(mark)
    await db_session.commit()

    response = await client.get(
        f"/api/videos/{sample_video.id}/marks",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_other_user_cannot_delete_mark(client, other_token, db_session, sample_video):
    """非擁有者無法刪除標記"""
    mark = Mark(
        video_id=sample_video.id,
        start_time=5.0,
        end_time=15.0,
        category="offense",
    )
    db_session.add(mark)
    await db_session.commit()
    await db_session.refresh(mark)

    response = await client.delete(
        f"/api/marks/{mark.id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403
