import json
import logging
import os
import shlex
import subprocess
import tempfile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.clip import Clip
from backend.models.highlight import Highlight, HighlightClip
from backend.models.mark import Mark, MarkPlayer

logger = logging.getLogger(__name__)

CATEGORY_LABELS = {
    "offense": "進攻",
    "defense": "防守",
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
    settings = get_settings()
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
    from backend.utils.streaming import validate_file_path
    os.makedirs(settings.highlight_dir, exist_ok=True)
    output_path = os.path.join(settings.highlight_dir, f"{highlight.id}.mp4")

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for clip in clips:
                # 驗證每個片段路徑
                validate_file_path(clip.file_path, settings.clip_dir)
                # 使用 shlex.quote() 轉義路徑
                f.write(f"file {shlex.quote(clip.file_path)}\n")
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
            timeout=settings.ffmpeg_timeout,
        )
        os.unlink(concat_file)

        highlight.file_path = output_path
        highlight.file_size = os.path.getsize(output_path)
        total_duration = sum(c.duration or 0 for c in clips)
        highlight.duration = total_duration
        highlight.status = "completed"

        # 產生縮圖
        from backend.services.thumbnail_service import generate_thumbnail, get_highlight_thumbnail_path
        thumb_path = get_highlight_thumbnail_path(highlight.id)
        if generate_thumbnail(output_path, thumb_path):
            highlight.thumbnail_path = thumb_path
    except subprocess.TimeoutExpired:
        highlight.status = "failed"
        highlight.error_message = "影片處理失敗（處理超時）"
        logger.error("FFmpeg 精華剪輯合併超時: highlight_id=%d", highlight.id)
    except subprocess.CalledProcessError as e:
        highlight.status = "failed"
        highlight.error_message = "影片處理失敗"
        stderr = e.stderr.decode(errors="replace")[:2000] if e.stderr else "unknown"
        logger.error("FFmpeg 精華剪輯合併失敗: highlight_id=%d, stderr=%s", highlight.id, stderr)
    except Exception as e:
        highlight.status = "failed"
        highlight.error_message = "影片處理失敗"
        logger.error("精華剪輯產出異常: highlight_id=%d, error=%s", highlight.id, str(e))

    await db.commit()
    await db.refresh(highlight)
    return highlight


async def delete_highlight(db: AsyncSession, highlight_id: int) -> None:
    """刪除精華剪輯：實體檔案 + 關聯分享 + DB 記錄"""
    from sqlalchemy.orm import selectinload

    stmt = select(Highlight).where(Highlight.id == highlight_id).options(
        selectinload(Highlight.clips),
        selectinload(Highlight.share_links),
    )
    result = await db.execute(stmt)
    highlight = result.scalar_one_or_none()
    if not highlight:
        return

    if highlight.file_path and os.path.exists(highlight.file_path):
        os.remove(highlight.file_path)
    if highlight.thumbnail_path and os.path.exists(highlight.thumbnail_path):
        os.remove(highlight.thumbnail_path)

    await db.delete(highlight)
    await db.commit()


async def batch_delete_highlights(db: AsyncSession, highlight_ids: list[int]) -> dict[str, int]:
    """批量刪除精華剪輯，回傳成功與失敗數量"""
    from sqlalchemy.orm import selectinload
    success = 0
    failed = 0

    for highlight_id in highlight_ids:
        stmt = select(Highlight).where(Highlight.id == highlight_id).options(
            selectinload(Highlight.clips),
            selectinload(Highlight.share_links),
        )
        result = await db.execute(stmt)
        highlight = result.scalar_one_or_none()
        if not highlight:
            failed += 1
            continue

        if highlight.file_path and os.path.exists(highlight.file_path):
            os.remove(highlight.file_path)
        if highlight.thumbnail_path and os.path.exists(highlight.thumbnail_path):
            os.remove(highlight.thumbnail_path)

        await db.delete(highlight)
        success += 1

    await db.commit()
    return {"success": success, "failed": failed}


async def list_highlights(
    db: AsyncSession, owner_id: int | None = None, limit: int = 100, offset: int = 0
) -> list[Highlight]:
    stmt = select(Highlight).order_by(Highlight.created_at.desc())
    if owner_id is not None:
        stmt = stmt.where(Highlight.owner_id == owner_id)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
