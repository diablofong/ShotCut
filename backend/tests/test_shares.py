"""分享連結 API 整合測試"""
import pytest
from datetime import datetime, timedelta, timezone

from backend.models.highlight import Highlight
from backend.models.share_link import ShareLink


@pytest.fixture
async def sample_highlight(db_session, regular_user):
    hl = Highlight(
        title="測試精華",
        status="completed",
        file_path="/tmp/test_highlight.mp4",
        owner_id=regular_user.id,
    )
    db_session.add(hl)
    await db_session.commit()
    await db_session.refresh(hl)
    return hl


@pytest.fixture
async def active_share(db_session, sample_highlight):
    share = ShareLink(
        highlight_id=sample_highlight.id,
        token="valid-share-token-abc123",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(share)
    await db_session.commit()
    await db_session.refresh(share)
    return share


@pytest.fixture
async def expired_share(db_session, sample_highlight):
    share = ShareLink(
        highlight_id=sample_highlight.id,
        token="expired-share-token-xyz789",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(share)
    await db_session.commit()
    await db_session.refresh(share)
    return share


@pytest.mark.asyncio
async def test_access_share_link_public(client, active_share):
    """公開存取分享連結不需要認證"""
    response = await client.get(f"/api/shares/{active_share.token}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_access_expired_share_link(client, expired_share):
    """過期分享連結回傳 410"""
    response = await client.get(f"/api/shares/{expired_share.token}")
    assert response.status_code == 410


@pytest.mark.asyncio
async def test_access_nonexistent_share_link(client):
    response = await client.get("/api/shares/nonexistent-token")
    assert response.status_code == 404
