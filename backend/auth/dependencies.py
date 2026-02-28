from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.auth.security import decode_access_token
from backend.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    # 若 Bearer header 沒有 token，嘗試從 query param 取得（供 img src URL 使用）
    effective_token = token or request.query_params.get("token")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認證失敗",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not effective_token:
        raise credentials_exception
    try:
        payload = decode_access_token(effective_token)
        user_id = int(payload["sub"])
    except Exception:
        raise credentials_exception

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise credentials_exception
    return user


async def get_current_user_from_token(token: str, db: AsyncSession) -> User:
    """用於 WebSocket 認證（直接傳入 token 字串）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認證失敗",
    )
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception:
        raise credentials_exception

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise credentials_exception
    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理員權限",
        )
    return current_user


async def verify_video_owner(video_id: int, db: AsyncSession, current_user: User):
    from backend.models.video import Video

    video = await db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="影片不存在")
    if current_user.role != "admin" and video.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="無權存取此影片")
    return video


async def verify_highlight_owner(highlight_id: int, db: AsyncSession, current_user: User):
    from backend.models.highlight import Highlight

    highlight = await db.get(Highlight, highlight_id)
    if not highlight:
        raise HTTPException(status_code=404, detail="精華剪輯不存在")
    if current_user.role != "admin" and highlight.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="無權存取此精華剪輯")
    return highlight
