from datetime import datetime

from sqlalchemy import ForeignKey, String, Float, BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.database import Base


class Clip(Base):
    __tablename__ = "clips"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    mark_id: Mapped[int] = mapped_column(ForeignKey("marks.id", ondelete="CASCADE"))
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/processing/completed/failed
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    video = relationship("Video", back_populates="clips")
    mark = relationship("Mark", back_populates="clip")
