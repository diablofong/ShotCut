import json
import os
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user, verify_highlight_owner
from backend.models.user import User
from backend.models.highlight import Highlight
from backend.services import highlight_service
from backend.utils.streaming import stream_file_response, validate_file_path

HIGHLIGHT_DIR = os.getenv("HIGHLIGHT_DIR", "./highlights")

router = APIRouter(tags=["highlights"])


class GenerateRequest(BaseModel):
    player_numbers: list[int] = []
    categories: list[str] = []
    title: str | None = None


class BatchDeleteRequest(BaseModel):
    ids: list[int]


class HighlightOut(BaseModel):
    id: int
    title: str
    file_path: str | None = None
    duration: float | None = None
    file_size: int | None = None
    status: str
    error_message: str | None = None
    player_numbers: list[int] = []
    categories: list[str] = []
    created_at: str | None = None

    model_config = {"from_attributes": True}


def _highlight_to_out(hl: Highlight) -> HighlightOut:
    player_numbers = []
    if hl.filter_players:
        try:
            player_numbers = json.loads(hl.filter_players)
        except (json.JSONDecodeError, TypeError):
            pass
    elif hl.filter_player is not None:
        player_numbers = [hl.filter_player]

    categories = []
    if hl.filter_categories:
        try:
            categories = json.loads(hl.filter_categories)
        except (json.JSONDecodeError, TypeError):
            pass
    elif hl.filter_category:
        categories = [hl.filter_category]

    return HighlightOut(
        id=hl.id,
        title=hl.title,
        file_path=hl.file_path,
        duration=hl.duration,
        file_size=hl.file_size,
        status=hl.status,
        error_message=hl.error_message,
        player_numbers=player_numbers,
        categories=categories,
        created_at=hl.created_at.isoformat() if hl.created_at else None,
    )


@router.post("/highlights/generate", response_model=HighlightOut)
async def generate_highlight(
    req: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = None if current_user.role == "admin" else current_user.id
    try:
        highlight = await highlight_service.generate_highlight(
            db,
            player_numbers=req.player_numbers or None,
            categories=req.categories or None,
            title=req.title,
            user_id=user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _highlight_to_out(highlight)


@router.get("/highlights/{highlight_id}/stream")
async def stream_highlight(
    highlight_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    highlight = await verify_highlight_owner(highlight_id, db, current_user)
    if not highlight.file_path or not os.path.exists(highlight.file_path):
        raise HTTPException(status_code=404, detail="精華剪輯檔案不存在")

    file_path = highlight.file_path
    validate_file_path(file_path, HIGHLIGHT_DIR)
    file_size = os.path.getsize(file_path)
    return stream_file_response(file_path, file_size, request.headers.get("range"))


@router.get("/highlights/{highlight_id}/download")
async def download_highlight(
    highlight_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    highlight = await verify_highlight_owner(highlight_id, db, current_user)
    if not highlight.file_path or not os.path.exists(highlight.file_path):
        raise HTTPException(status_code=404, detail="精華剪輯檔案不存在")
    validate_file_path(highlight.file_path, HIGHLIGHT_DIR)
    filename = f"{highlight.title}.mp4"
    encoded = quote(filename)
    return FileResponse(
        highlight.file_path, media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )


@router.get("/highlights/{highlight_id}/thumbnail")
async def highlight_thumbnail(
    highlight_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.services.thumbnail_service import generate_thumbnail, get_highlight_thumbnail_path

    highlight = await verify_highlight_owner(highlight_id, db, current_user)
    # Lazy 生成
    if not highlight.thumbnail_path or not os.path.exists(highlight.thumbnail_path):
        if highlight.file_path and os.path.exists(highlight.file_path):
            thumb_path = get_highlight_thumbnail_path(highlight.id)
            if generate_thumbnail(highlight.file_path, thumb_path):
                highlight.thumbnail_path = thumb_path
                await db.commit()
    if not highlight.thumbnail_path or not os.path.exists(highlight.thumbnail_path):
        raise HTTPException(status_code=404, detail="縮圖不存在")
    return FileResponse(highlight.thumbnail_path, media_type="image/jpeg")


@router.delete("/highlights/{highlight_id}")
async def delete_highlight(
    highlight_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    highlight = await db.get(Highlight, highlight_id)
    if not highlight:
        raise HTTPException(status_code=404, detail="精華剪輯不存在")
    if current_user.role != "admin" and highlight.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="無權刪除此精華剪輯")
    await highlight_service.delete_highlight(db, highlight_id)
    return {"detail": "已刪除"}


@router.post("/highlights/batch/delete")
async def batch_delete_highlights(
    req: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量刪除精華剪輯"""
    if not req.ids:
        raise HTTPException(status_code=400, detail="未指定任何 ID")

    # 驗證權限：一般使用者只能刪除自己的精華剪輯
    for highlight_id in req.ids:
        highlight = await db.get(Highlight, highlight_id)
        if highlight and current_user.role != "admin" and highlight.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="無權刪除部分精華剪輯")

    result = await highlight_service.batch_delete_highlights(db, req.ids)
    return {"detail": f"成功刪除 {result['success']} 筆，失敗 {result['failed']} 筆", **result}


@router.get("/highlights", response_model=list[HighlightOut])
async def list_highlights(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        highlights = await highlight_service.list_highlights(db, limit=limit, offset=offset)
    else:
        highlights = await highlight_service.list_highlights(db, owner_id=current_user.id, limit=limit, offset=offset)
    return [_highlight_to_out(hl) for hl in highlights]
