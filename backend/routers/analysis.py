from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user, verify_video_owner
from backend.models.candidate import Candidate
from backend.models.user import User
from backend.services import audio_service

router = APIRouter(tags=["analysis"])


class AnalyzeRequest(BaseModel):
    sensitivity: float = 0.5
    min_interval: float = 2.0


class CandidateOut(BaseModel):
    id: int
    video_id: int
    timestamp: float
    type: str
    confidence: float

    model_config = {"from_attributes": True}


@router.post("/videos/{video_id}/analyze", response_model=list[CandidateOut])
async def analyze_video(
    video_id: int,
    req: AnalyzeRequest = AnalyzeRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_video_owner(video_id, db, current_user)
    try:
        candidates = await audio_service.analyze_video(
            db, video_id, req.sensitivity, req.min_interval
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = await db.execute(
        select(Candidate).where(Candidate.video_id == video_id).order_by(Candidate.timestamp)
    )
    return list(result.scalars().all())


@router.get("/videos/{video_id}/candidates", response_model=list[CandidateOut])
async def get_candidates(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_video_owner(video_id, db, current_user)
    result = await db.execute(
        select(Candidate).where(Candidate.video_id == video_id).order_by(Candidate.timestamp)
    )
    return list(result.scalars().all())
