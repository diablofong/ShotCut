from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.database import get_db
from backend.models.mark import Mark, MarkPlayer

router = APIRouter(tags=["marks"])


class MarkCreate(BaseModel):
    start_time: float
    end_time: float
    category: str = "untagged"
    player_numbers: list[int] = []


class MarkUpdate(BaseModel):
    start_time: float | None = None
    end_time: float | None = None
    category: str | None = None
    player_numbers: list[int] | None = None


class MarkOut(BaseModel):
    id: int
    video_id: int
    start_time: float
    end_time: float
    category: str
    player_numbers: list[int] = []

    model_config = {"from_attributes": True}


def _mark_to_out(mark: Mark) -> MarkOut:
    return MarkOut(
        id=mark.id,
        video_id=mark.video_id,
        start_time=mark.start_time,
        end_time=mark.end_time,
        category=mark.category,
        player_numbers=[p.player_number for p in mark.players],
    )


@router.post("/videos/{video_id}/marks", response_model=MarkOut)
async def create_mark(
    video_id: int,
    req: MarkCreate,
    db: AsyncSession = Depends(get_db),
):
    valid_categories = {"offense", "defense", "highlight", "turnover", "untagged"}
    if req.category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"分類必須為: {', '.join(valid_categories)}")

    mark = Mark(
        video_id=video_id,
        start_time=req.start_time,
        end_time=req.end_time,
        category=req.category,
    )
    db.add(mark)
    await db.flush()

    for num in req.player_numbers:
        db.add(MarkPlayer(mark_id=mark.id, player_number=num))

    await db.commit()

    result = await db.execute(
        select(Mark).options(selectinload(Mark.players)).where(Mark.id == mark.id)
    )
    mark = result.scalar_one()
    return _mark_to_out(mark)


@router.get("/videos/{video_id}/marks", response_model=list[MarkOut])
async def list_marks(video_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Mark)
        .options(selectinload(Mark.players))
        .where(Mark.video_id == video_id)
        .order_by(Mark.start_time)
    )
    return [_mark_to_out(m) for m in result.scalars().all()]


@router.put("/marks/{mark_id}", response_model=MarkOut)
async def update_mark(
    mark_id: int,
    req: MarkUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Mark).options(selectinload(Mark.players)).where(Mark.id == mark_id)
    )
    mark = result.scalar_one_or_none()
    if not mark:
        raise HTTPException(status_code=404, detail="標記不存在")

    if req.start_time is not None:
        mark.start_time = req.start_time
    if req.end_time is not None:
        mark.end_time = req.end_time
    if req.category is not None:
        mark.category = req.category

    if req.player_numbers is not None:
        # 清除舊的球員關聯
        for p in mark.players:
            await db.delete(p)
        await db.flush()
        for num in req.player_numbers:
            db.add(MarkPlayer(mark_id=mark.id, player_number=num))

    await db.commit()

    result = await db.execute(
        select(Mark).options(selectinload(Mark.players)).where(Mark.id == mark_id)
    )
    mark = result.scalar_one()
    return _mark_to_out(mark)


@router.delete("/marks/{mark_id}")
async def delete_mark(mark_id: int, db: AsyncSession = Depends(get_db)):
    mark = await db.get(Mark, mark_id)
    if not mark:
        raise HTTPException(status_code=404, detail="標記不存在")
    await db.delete(mark)
    await db.commit()
    return {"ok": True}
