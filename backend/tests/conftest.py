"""
測試共用 fixtures：
- 使用 SQLite in-memory 作為測試資料庫（不依賴 MariaDB）
- 每個測試函式獨立的資料庫 session
- 提供認證 client（admin / 一般用戶）
- mock_storage：模擬 S3StorageService，不依賴真實 MinIO
"""
import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# 強制測試環境使用 SQLite（覆寫 Docker 容器的 DATABASE_URL，S3 驗證在 SQLite 模式下跳過）
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("CORS_ORIGINS", "")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test-access-key")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test-secret-key")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")

from backend.db.database import Base, get_db
from backend.main import app
from backend.auth.security import hash_password, create_access_token
from backend.models.user import User
from backend.models.video import Video
from backend.models.mark import Mark, MarkPlayer  # noqa: F401
from backend.models.clip import Clip  # noqa: F401
from backend.models.highlight import Highlight  # noqa: F401
from backend.models.share_link import ShareLink  # noqa: F401
from backend.models.refresh_token import RefreshToken  # noqa: F401

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session):
    """提供已注入測試 DB 的 AsyncClient"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def admin_user(db_session) -> User:
    user = User(
        username="admin",
        hashed_password=hash_password("adminpass"),
        display_name="管理員",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def regular_user(db_session) -> User:
    user = User(
        username="user1",
        hashed_password=hash_password("userpass"),
        display_name="一般用戶",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def other_user(db_session) -> User:
    user = User(
        username="user2",
        hashed_password=hash_password("userpass2"),
        display_name="另一個用戶",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_token(admin_user) -> str:
    return create_access_token(admin_user.id, admin_user.role)


@pytest.fixture(scope="function")
def user_token(regular_user) -> str:
    return create_access_token(regular_user.id, regular_user.role)


@pytest.fixture(scope="function")
def other_token(other_user) -> str:
    return create_access_token(other_user.id, other_user.role)


@pytest.fixture(scope="function")
async def sample_video(db_session, regular_user) -> Video:
    video = Video(
        title="測試影片",
        source_type="upload",
        status="completed",
        file_path="/tmp/test.mp4",  # nosec B108
        owner_id=regular_user.id,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    return video


@pytest.fixture(scope="function")
async def r2_video(db_session, regular_user) -> Video:
    """擁有 r2_key 的影片（S3 上傳完成狀態）"""
    video = Video(
        title="S3 測試影片",
        source_type="upload",
        status="completed",
        r2_key="videos/2026/test_video.mp4",
        thumbnail_path="thumbnails/video_1_thumb.jpg",
        owner_id=regular_user.id,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    return video


@pytest.fixture(scope="function")
def mock_storage():
    """Mock S3StorageService，測試不依賴真實 S3/MinIO"""
    storage = MagicMock()
    storage.upload_file = AsyncMock(return_value=True)
    storage.delete_object = AsyncMock(return_value=True)
    storage.generate_presigned_put_url = AsyncMock(
        return_value="https://mock-s3.example.com/presigned-put?sig=test"
    )
    storage.generate_presigned_get_url = AsyncMock(
        return_value="https://mock-s3.example.com/presigned-get?sig=test"
    )

    # video_service 內部是 local import，patch 源頭 storage_service 即可覆蓋
    targets = [
        "backend.services.storage_service.get_storage_service",
        "backend.routers.videos.get_storage_service",
    ]
    patchers = [patch(t, return_value=storage) for t in targets]
    for p in patchers:
        p.start()
    yield storage
    for p in patchers:
        p.stop()
