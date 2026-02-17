from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user, verify_video_owner
from backend.models.mark import Mark, MarkPlayer
from backend.models.user import User

router = APIRouter(tags=["marks"])

CATEGORY_LABELS = {
    "offense": "進攻",
    "defense": "防守",
    "turnover": "失誤",
    "untagged": "未分類",
}


class PlayerInfo(BaseModel):
    number: int
    name: str = ""


class MarkCreate(BaseModel):
    # 方式 1（舊）：時間點 + 偏移
    time: float | None = None
    start_offset: float = 8.0
    end_offset: float = 5.0
    # 方式 2（新）：直接範圍
    start_time: float | None = None
    end_time: float | None = None
    # 共用
    category: str = "untagged"
    label: str = ""
    player_numbers: list[int] = []
    players: list[PlayerInfo] = []


class MarkUpdate(BaseModel):
    time: float | None = None
    start_offset: float | None = None
    end_offset: float | None = None
    start_time: float | None = None
    end_time: float | None = None
    category: str | None = None
    label: str | None = None
    player_numbers: list[int] | None = None
    players: list[PlayerInfo] | None = None


class PlayerOut(BaseModel):
    number: int
    name: str


class MarkOut(BaseModel):
    id: int
    video_id: int
    time: float
    start_time: float
    end_time: float
    start_offset: float
    end_offset: float
    category: str
    label: str
    player_numbers: list[int] = []
    players: list[PlayerOut] = []

    model_config = {"from_attributes": True}


def _mark_to_out(mark: Mark) -> MarkOut:
    time = (mark.start_time + mark.end_time) / 2
    return MarkOut(
        id=mark.id,
        video_id=mark.video_id,
        time=time,
        start_time=mark.start_time,
        end_time=mark.end_time,
        start_offset=round(time - mark.start_time, 2),
        end_offset=round(mark.end_time - time, 2),
        category=mark.category,
        label=mark.label or CATEGORY_LABELS.get(mark.category, mark.category),
        player_numbers=[p.player_number for p in mark.players],
        players=[PlayerOut(number=p.player_number, name=p.player_name or "") for p in mark.players],
    )


@router.post("/videos/{video_id}/marks", response_model=MarkOut)
async def create_mark(
    video_id: int,
    req: MarkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_video_owner(video_id, db, current_user)

    valid_categories = {"offense", "defense", "turnover", "untagged"}
    if req.category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"分類必須為: {', '.join(valid_categories)}")

    if req.start_time is not None and req.end_time is not None:
        start_time = req.start_time
        end_time = req.end_time
    elif req.time is not None:
        start_time = max(0, req.time - req.start_offset)
        end_time = req.time + req.end_offset
    else:
        raise HTTPException(status_code=400, detail="需提供 start_time/end_time 或 time")
    label = req.label or CATEGORY_LABELS.get(req.category, req.category)

    mark = Mark(
        video_id=video_id,
        start_time=start_time,
        end_time=end_time,
        category=req.category,
        label=label,
    )
    db.add(mark)
    await db.flush()

    if req.players:
        for p in req.players:
            db.add(MarkPlayer(mark_id=mark.id, player_number=p.number, player_name=p.name))
    else:
        for num in req.player_numbers:
            db.add(MarkPlayer(mark_id=mark.id, player_number=num))

    await db.commit()

    result = await db.execute(
        select(Mark).options(selectinload(Mark.players)).where(Mark.id == mark.id)
    )
    mark = result.scalar_one()
    return _mark_to_out(mark)


@router.get("/videos/{video_id}/marks", response_model=list[MarkOut])
async def list_marks(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_video_owner(video_id, db, current_user)
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
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Mark).options(selectinload(Mark.players)).where(Mark.id == mark_id)
    )
    mark = result.scalar_one_or_none()
    if not mark:
        raise HTTPException(status_code=404, detail="標記不存在")

    await verify_video_owner(mark.video_id, db, current_user)

    if req.time is not None:
        s_off = req.start_offset if req.start_offset is not None else 3.0
        e_off = req.end_offset if req.end_offset is not None else 3.0
        mark.start_time = max(0, req.time - s_off)
        mark.end_time = req.time + e_off
    else:
        if req.start_time is not None:
            mark.start_time = req.start_time
        if req.end_time is not None:
            mark.end_time = req.end_time

    if req.category is not None:
        mark.category = req.category
    if req.label is not None:
        mark.label = req.label

    if req.players is not None:
        for p in mark.players:
            await db.delete(p)
        await db.flush()
        for p in req.players:
            db.add(MarkPlayer(mark_id=mark.id, player_number=p.number, player_name=p.name))
    elif req.player_numbers is not None:
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
async def delete_mark(
    mark_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mark = await db.get(Mark, mark_id)
    if not mark:
        raise HTTPException(status_code=404, detail="標記不存在")

    await verify_video_owner(mark.video_id, db, current_user)

    await db.delete(mark)
    await db.commit()
    return {"ok": True}
