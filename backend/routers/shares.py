import secrets
import os
from datetime import datetime, timedelta
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.share_link import ShareLink
from backend.models.highlight import Highlight
from backend.models.user import User

router = APIRouter(tags=["shares"])


class ExpirationOption(str, Enum):
    ONE_DAY = "1d"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    NEVER = "never"


EXPIRATION_DELTAS = {
    ExpirationOption.ONE_DAY: timedelta(days=1),
    ExpirationOption.SEVEN_DAYS: timedelta(days=7),
    ExpirationOption.THIRTY_DAYS: timedelta(days=30),
    ExpirationOption.NEVER: None,
}


class ShareCreate(BaseModel):
    highlight_id: int
    expiration: ExpirationOption = ExpirationOption.SEVEN_DAYS


class ShareOut(BaseModel):
    id: int
    highlight_id: int
    token: str
    access_count: int
    expires_at: str | None = None

    model_config = {"from_attributes": True}


def _check_share_expiration(share: ShareLink):
    """檢查分享連結是否已過期"""
    if share.expires_at and datetime.utcnow() > share.expires_at:
        raise HTTPException(status_code=410, detail="此分享連結已過期")


@router.post("/shares", response_model=ShareOut)
async def create_share(
    req: ShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    highlight = await db.get(Highlight, req.highlight_id)
    if not highlight:
        raise HTTPException(status_code=404, detail="精華剪輯不存在")

    if current_user.role != "admin" and highlight.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="無權分享此精華剪輯")

    token = secrets.token_urlsafe(32)
    delta = EXPIRATION_DELTAS[req.expiration]
    expires_at = datetime.utcnow() + delta if delta else None
    share = ShareLink(highlight_id=req.highlight_id, token=token, expires_at=expires_at)
    db.add(share)
    await db.commit()
    await db.refresh(share)
    return ShareOut(
        id=share.id,
        highlight_id=share.highlight_id,
        token=share.token,
        access_count=share.access_count,
        expires_at=share.expires_at.isoformat() if share.expires_at else None,
    )


@router.get("/shares/{token}")
async def get_share(token: str, db: AsyncSession = Depends(get_db)):
    """公開端點：透過 token 取得分享資訊，不需登入"""
    result = await db.execute(select(ShareLink).where(ShareLink.token == token))
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="分享連結不存在")

    _check_share_expiration(share)

    share.access_count += 1
    await db.commit()

    highlight = await db.get(Highlight, share.highlight_id)
    if not highlight:
        raise HTTPException(status_code=404, detail="精華剪輯不存在")

    return {
        "id": share.id,
        "highlight_id": share.highlight_id,
        "token": share.token,
        "access_count": share.access_count,
        "expires_at": share.expires_at.isoformat() if share.expires_at else None,
        "highlight": {
            "id": highlight.id,
            "title": highlight.title,
            "file_path": highlight.file_path,
        },
    }


@router.get("/shares/{token}/stream")
async def stream_share(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """公開端點：透過 token 串流影片，不需登入，支援 Range 請求"""
    result = await db.execute(select(ShareLink).where(ShareLink.token == token))
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="分享連結不存在")

    _check_share_expiration(share)

    highlight = await db.get(Highlight, share.highlight_id)
    if not highlight or not highlight.file_path or not os.path.exists(highlight.file_path):
        raise HTTPException(status_code=404, detail="影片檔案不存在")

    file_path = highlight.file_path
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    if range_header:
        range_spec = range_header.replace("bytes=", "")
        parts = range_spec.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
        end = min(end, file_size - 1)
        content_length = end - start + 1

        def iter_file():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk = f.read(min(8192, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            iter_file(),
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
            },
        )

    return FileResponse(
        file_path,
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"},
    )


@router.get("/shares/{token}/thumbnail")
async def share_thumbnail(token: str, db: AsyncSession = Depends(get_db)):
    """公開端點：透過 token 取得精華剪輯縮圖"""
    result = await db.execute(select(ShareLink).where(ShareLink.token == token))
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="分享連結不存在")

    _check_share_expiration(share)

    highlight = await db.get(Highlight, share.highlight_id)
    if not highlight or not highlight.thumbnail_path or not os.path.exists(highlight.thumbnail_path):
        raise HTTPException(status_code=404, detail="縮圖不存在")

    return FileResponse(highlight.thumbnail_path, media_type="image/jpeg")


@router.delete("/shares/{share_id}")
async def delete_share(
    share_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    share = await db.get(ShareLink, share_id)
    if not share:
        raise HTTPException(status_code=404, detail="分享連結不存在")

    highlight = await db.get(Highlight, share.highlight_id)
    if current_user.role != "admin" and (not highlight or highlight.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="無權刪除此分享連結")

    await db.delete(share)
    await db.commit()
    return {"ok": True}
