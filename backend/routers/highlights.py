from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
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
async def generate_highlight(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    try:
        highlight = await highlight_service.generate_highlight(
            db,
            player_number=req.player_number,
            category=req.category,
            title=req.title,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return highlight


@router.get("/highlights", response_model=list[HighlightOut])
async def list_highlights(db: AsyncSession = Depends(get_db)):
    return await highlight_service.list_highlights(db)
