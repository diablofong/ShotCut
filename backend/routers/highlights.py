from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.user import User
from backend.services import highlight_service

router = APIRouter(tags=["highlights"])


class GenerateRequest(BaseModel):
    player_number: int | None = None
    category: str | None = None
    title: str | None = None


class HighlightOut(BaseModel):
    id: int
    title: str
    filter_player: int | None = None
    filter_category: str | None = None
    file_path: str | None = None
    duration: float | None = None
    file_size: int | None = None
    status: str
    error_message: str | None = None

    model_config = {"from_attributes": True}


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
            player_number=req.player_number,
            category=req.category,
            title=req.title,
            user_id=user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return highlight


@router.get("/highlights", response_model=list[HighlightOut])
async def list_highlights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return await highlight_service.list_highlights(db)
    return await highlight_service.list_highlights(db, owner_id=current_user.id)
