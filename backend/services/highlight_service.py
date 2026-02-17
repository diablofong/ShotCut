import json
import os
import subprocess
import tempfile

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.clip import Clip
from backend.models.highlight import Highlight, HighlightClip
from backend.models.mark import Mark, MarkPlayer

HIGHLIGHT_DIR = os.getenv("HIGHLIGHT_DIR", "./highlights")

CATEGORY_LABELS = {
    "offense": "進攻",
    "defense": "防守",
    "highlight": "精彩",
    "turnover": "失誤",
}


async def generate_highlight(
    db: AsyncSession,
    player_numbers: list[int] | None = None,
    categories: list[str] | None = None,
    title: str | None = None,
    user_id: int | None = None,
) -> Highlight:
    """依球員/標籤篩選片段，合併為精華剪輯（支援多選）"""
    from backend.models.video import Video
    stmt = select(Clip).where(Clip.status == "completed").join(Mark).join(Video)

    if user_id is not None:
        stmt = stmt.where(Video.owner_id == user_id)

    if categories:
        stmt = stmt.where(Mark.category.in_(categories))

    if player_numbers:
        stmt = stmt.join(MarkPlayer, Mark.id == MarkPlayer.mark_id).where(
            MarkPlayer.player_number.in_(player_numbers)
        )

    stmt = stmt.order_by(Mark.start_time)
    result = await db.execute(stmt)
    clips = list(result.scalars().unique().all())

    if not clips:
        raise ValueError("無符合條件的片段")

    # 自動產生標題
    if not title:
        parts = []
        if player_numbers:
            parts.append("球員" + ",".join(str(n) for n in player_numbers))
        if categories:
            cat_labels = [CATEGORY_LABELS.get(c, c) for c in categories]
            parts.append("+".join(cat_labels))
        title = " ".join(parts) + " 精華剪輯" if parts else "精華剪輯"

    highlight = Highlight(
        title=title,
        filter_player=player_numbers[0] if player_numbers and len(player_numbers) == 1 else None,
        filter_category=categories[0] if categories and len(categories) == 1 else None,
        filter_players=json.dumps(player_numbers) if player_numbers else None,
        filter_categories=json.dumps(categories) if categories else None,
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
        total_duration = sum(c.duration or 0 for c in clips)
        highlight.duration = total_duration
        highlight.status = "completed"
    except Exception as e:
        highlight.status = "failed"
        highlight.error_message = str(e)[:2000]

    await db.commit()
    await db.refresh(highlight)
    return highlight


async def delete_highlight(db: AsyncSession, highlight_id: int) -> None:
    """刪除精華剪輯：實體檔案 + 關聯分享 + DB 記錄"""
    from backend.models.share import ShareLink

    highlight = await db.get(Highlight, highlight_id)
    if not highlight:
        return

    # 刪除實體檔案
    if highlight.file_path and os.path.exists(highlight.file_path):
        os.remove(highlight.file_path)

    # 刪除關聯的分享連結
    stmt = select(ShareLink).where(ShareLink.highlight_id == highlight_id)
    result = await db.execute(stmt)
    for share in result.scalars().all():
        await db.delete(share)

    # 刪除關聯的 HighlightClip
    stmt = select(HighlightClip).where(HighlightClip.highlight_id == highlight_id)
    result = await db.execute(stmt)
    for hc in result.scalars().all():
        await db.delete(hc)

    await db.delete(highlight)
    await db.commit()


async def list_highlights(db: AsyncSession, owner_id: int | None = None) -> list[Highlight]:
    stmt = select(Highlight).order_by(Highlight.created_at.desc())
    if owner_id is not None:
        stmt = stmt.where(Highlight.owner_id == owner_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
