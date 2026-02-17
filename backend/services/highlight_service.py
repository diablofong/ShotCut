import os
import subprocess
import tempfile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.clip import Clip
from backend.models.highlight import Highlight, HighlightClip
from backend.models.mark import Mark, MarkPlayer

HIGHLIGHT_DIR = os.getenv("HIGHLIGHT_DIR", "./highlights")


async def generate_highlight(
    db: AsyncSession,
    player_number: int | None = None,
    category: str | None = None,
    title: str | None = None,
    user_id: int | None = None,
) -> Highlight:
    """依球員/標籤篩選片段，合併為精華剪輯"""
    # 篩選符合條件的片段
    from backend.models.video import Video
    stmt = select(Clip).where(Clip.status == "completed").join(Mark).join(Video)

    if user_id is not None:
        stmt = stmt.where(Video.owner_id == user_id)

    if category:
        stmt = stmt.where(Mark.category == category)

    if player_number is not None:
        stmt = stmt.join(MarkPlayer, Mark.id == MarkPlayer.mark_id).where(
            MarkPlayer.player_number == player_number
        )

    stmt = stmt.order_by(Mark.start_time)
    result = await db.execute(stmt)
    clips = list(result.scalars().all())

    if not clips:
        raise ValueError("無符合條件的片段")

    # 建立 highlight 記錄
    if not title:
        parts = []
        if player_number is not None:
            parts.append(f"球員{player_number}")
        if category:
            parts.append(category)
        title = " ".join(parts) + " 精華剪輯" if parts else "精華剪輯"

    highlight = Highlight(
        title=title,
        filter_player=player_number,
        filter_category=category,
        status="processing",
        owner_id=user_id,
    )
    db.add(highlight)
    await db.commit()
    await db.refresh(highlight)

    # 建立關聯
    for i, clip in enumerate(clips):
        db.add(HighlightClip(highlight_id=highlight.id, clip_id=clip.id, order=i))
    await db.commit()

    # FFmpeg concat
    os.makedirs(HIGHLIGHT_DIR, exist_ok=True)
    output_path = os.path.join(HIGHLIGHT_DIR, f"{highlight.id}.mp4")

    try:
        # 建立 concat 清單檔案
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for clip in clips:
                f.write(f"file '{clip.file_path}'\n")
            concat_file = f.name

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                output_path,
            ],
            capture_output=True,
            check=True,
        )
        os.unlink(concat_file)

        highlight.file_path = output_path
        highlight.file_size = os.path.getsize(output_path)
        # 計算總時長
        total_duration = sum(c.duration or 0 for c in clips)
        highlight.duration = total_duration
        highlight.status = "completed"
    except Exception as e:
        highlight.status = "failed"
        highlight.error_message = str(e)[:2000]

    await db.commit()
    await db.refresh(highlight)
    return highlight


async def list_highlights(db: AsyncSession, owner_id: int | None = None) -> list[Highlight]:
    stmt = select(Highlight).order_by(Highlight.created_at.desc())
    if owner_id is not None:
        stmt = stmt.where(Highlight.owner_id == owner_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
