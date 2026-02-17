import secrets
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.share_link import ShareLink
from backend.models.highlight import Highlight
from backend.models.user import User

router = APIRouter(tags=["shares"])


class ShareCreate(BaseModel):
    highlight_id: int


class ShareOut(BaseModel):
    id: int
    highlight_id: int
    token: str
    access_count: int

    model_config = {"from_attributes": True}


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
    share = ShareLink(highlight_id=req.highlight_id, token=token)
    db.add(share)
    await db.commit()
    await db.refresh(share)
    return share


@router.get("/shares/{token}")
async def get_share(token: str, db: AsyncSession = Depends(get_db)):
    """公開端點：透過 token 存取分享內容，不需登入"""
    result = await db.execute(select(ShareLink).where(ShareLink.token == token))
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="分享連結不存在")

    share.access_count += 1
    await db.commit()

    highlight = await db.get(Highlight, share.highlight_id)
    if not highlight or not highlight.file_path or not os.path.exists(highlight.file_path):
        raise HTTPException(status_code=404, detail="影片檔案不存在")

    return FileResponse(
        highlight.file_path,
        media_type="video/mp4",
        filename=f"{highlight.title}.mp4",
    )


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
