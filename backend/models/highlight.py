from datetime import datetime

from sqlalchemy import ForeignKey, String, Float, Integer, BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.database import Base


class Highlight(Base):
    __tablename__ = "highlights"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500))
    filter_player: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filter_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/processing/completed/failed
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    clips = relationship("HighlightClip", back_populates="highlight", cascade="all, delete-orphan")
    share_links = relationship("ShareLink", back_populates="highlight", cascade="all, delete-orphan")


class HighlightClip(Base):
    __tablename__ = "highlight_clips"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    highlight_id: Mapped[int] = mapped_column(ForeignKey("highlights.id", ondelete="CASCADE"))
    clip_id: Mapped[int] = mapped_column(ForeignKey("clips.id", ondelete="CASCADE"))
    order: Mapped[int] = mapped_column(Integer)

    highlight = relationship("Highlight", back_populates="clips")
    clip = relationship("Clip")
