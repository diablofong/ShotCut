from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.auth.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
)
from backend.auth.dependencies import get_current_user
from backend.config import get_settings
from backend.limiter import limiter
from backend.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"
_REFRESH_MAX_AGE = 60 * 60 * 24 * 7  # 7 天（秒）


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserMeOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("/login", response_model=TokenOut)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號已停用",
        )

    access_token = create_access_token(user.id, user.role)
    refresh_token = await create_refresh_token(db, user.id)

    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=_REFRESH_MAX_AGE,
        secure=False,  # 生產環境應設為 True（HTTPS）
    )

    return TokenOut(
        access_token=access_token,
        user={
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
        },
    )


@router.post("/refresh")
async def refresh_access_token(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=_REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少 refresh token")

    rt = await verify_refresh_token(db, refresh_token)
    if not rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token 無效或已過期")

    user = await db.get(User, rt.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="認證失敗")

    new_access_token = create_access_token(user.id, user.role)
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=_REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if refresh_token:
        await revoke_refresh_token(db, refresh_token)
    response.delete_cookie(key=_REFRESH_COOKIE)
    return {"detail": "已登出"}


@router.get("/me", response_model=UserMeOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
