from datetime import datetime

from sqlalchemy import ForeignKey, String, Float, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.database import Base


class Mark(Base):
    __tablename__ = "marks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(20), default="untagged")  # offense/defense/highlight/turnover/untagged
    label: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    video = relationship("Video", back_populates="marks")
    players = relationship("MarkPlayer", back_populates="mark", cascade="all, delete-orphan")
    clip = relationship("Clip", back_populates="mark", uselist=False, cascade="all, delete-orphan")


class MarkPlayer(Base):
    __tablename__ = "mark_players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mark_id: Mapped[int] = mapped_column(ForeignKey("marks.id", ondelete="CASCADE"))
    player_number: Mapped[int] = mapped_column(Integer)

    mark = relationship("Mark", back_populates="players")
