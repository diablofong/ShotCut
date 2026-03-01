from fastapi import APIRouter

from backend.config import get_settings

router = APIRouter(tags=["config"])


@router.get("/config")
async def get_config():
    """回傳前端 runtime 設定（不含任何 credentials）"""
    settings = get_settings()
    return {
        "features": {
            "clips": settings.enable_clips,
            "highlights": settings.enable_highlights,
            "sharing": settings.enable_sharing,
        }
    }
