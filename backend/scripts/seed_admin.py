import asyncio
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.auth.security import hash_password
from backend.models.user import User


async def seed():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("環境變數 DATABASE_URL 未設定")
    engine = create_async_engine(db_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        result = await db.execute(select(User).where(User.role == "admin").limit(1))
        if result.scalar_one_or_none():
            print("管理員帳號已存在，跳過種子")
            await engine.dispose()
            return

        username = os.getenv("ADMIN_USERNAME")
        password = os.getenv("ADMIN_PASSWORD")
        if not username or not password:
            raise RuntimeError("環境變數 ADMIN_USERNAME 與 ADMIN_PASSWORD 未設定")
        admin = User(
            username=username,
            hashed_password=hash_password(password),
            display_name="系統管理員",
            role="admin",
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print(f"已建立初始管理員帳號: {username}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
