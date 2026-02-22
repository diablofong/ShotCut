"""
測試共用 fixtures：
- 使用 SQLite in-memory 作為測試資料庫（不依賴 MariaDB）
- 每個測試函式獨立的資料庫 session
- 提供認證 client（admin / 一般用戶）
"""
import os
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# 設定測試環境變數（必須在匯入 app 之前）
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("CORS_ORIGINS", "")

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
