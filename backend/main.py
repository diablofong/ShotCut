import json
import logging
import os
import signal
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text, update

from backend.config import get_settings
from backend.db.database import engine, async_session
from backend.limiter import limiter
from backend.models.video import Video
from backend.routers import auth, users, videos, marks, clips, highlights, shares
from backend.routers import config as config_router

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


# ── JSON Logging ───────────────────────────────────────────────────
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": request_id_var.get(""),
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def _setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


_setup_logging()
logger = logging.getLogger(__name__)


# ── Startup 清理：將異常狀態的影片重設 ─────────────────────────────
async def _cleanup_stale_videos():
    """啟動時清理：downloading 重設為 failed；超過 1h 的 pending/processing 重設為 failed；刪除過期 refresh token"""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import delete as sa_delete
    from backend.models.refresh_token import RefreshToken
    try:
        async with async_session() as db:
            now = datetime.now(timezone.utc)
            one_hour_ago = now - timedelta(hours=1)
            await db.execute(
                update(Video)
                .where(Video.status == "downloading")
                .values(status="failed", error_message="服務重啟，下載中斷")
            )
            await db.execute(
                update(Video)
                .where(Video.status.in_(["pending", "processing"]))
                .where(Video.created_at < one_hour_ago)
                .values(status="failed", error_message="上傳逾時")
            )
            # 清理過期的 refresh token 記錄
            await db.execute(sa_delete(RefreshToken).where(RefreshToken.expires_at < now))
            await db.commit()
            logger.info("啟動清理完成")
    except Exception as e:
        logger.warning("啟動清理失敗: %s", str(e))


# ── Lifespan ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await _cleanup_stale_videos()
    yield
    await engine.dispose()


# ── App 初始化 ─────────────────────────────────────────────────────
app = FastAPI(title="ShotCut API", version="2.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)


# ── Security Headers Middleware ───────────────────────────────────
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ── JSON Logging Middleware ────────────────────────────────────────
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_var.set(req_id)
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000, 1)
    log_obj = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "level": "INFO",
        "logger": "access",
        "request_id": req_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
    }
    print(json.dumps(log_obj, ensure_ascii=False), flush=True)
    request_id_var.reset(token)
    response.headers["X-Request-ID"] = req_id
    return response


# ── Health 端點 ───────────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
async def health_check():
    from datetime import datetime, timezone
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "ok", "timestamp": timestamp}
    except Exception as e:
        logger.error("健康檢查資料庫連線失敗: %s", str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "error", "timestamp": timestamp},
        )


# ── Rate Limit Handler ─────────────────────────────────────────────
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "請求過於頻繁，請稍後再試"},
        headers={"Retry-After": str(exc.retry_after) if hasattr(exc, "retry_after") else "60"},
    )


# ── Routers ───────────────────────────────────────────────────────
app.include_router(config_router.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(marks.router, prefix="/api")
app.include_router(clips.router, prefix="/api")
app.include_router(highlights.router, prefix="/api")
app.include_router(shares.router, prefix="/api")


# ── SIGTERM Handler ───────────────────────────────────────────────
def _handle_sigterm(signum, frame):
    logger.info("收到 SIGTERM，開始 graceful shutdown")
    try:
        import asyncio as _asyncio
        loop = _asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_cleanup_stale_videos())
    except Exception:
        pass


signal.signal(signal.SIGTERM, _handle_sigterm)


# ── 前端靜態檔案 ──────────────────────────────────────────────────
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    index_html = os.path.join(frontend_dist, "index.html")
    frontend_dist_real = os.path.realpath(frontend_dist)

    @app.get("/favicon.svg")
    async def favicon():
        return FileResponse(os.path.join(frontend_dist, "favicon.svg"))

    @app.get("/{full_path:path}")
    async def spa_fallback(request: Request, full_path: str):
        file_path = os.path.realpath(os.path.join(frontend_dist, full_path))
        if (
            full_path
            and file_path.startswith(frontend_dist_real + os.sep)
            and os.path.isfile(file_path)
        ):
            return FileResponse(file_path)
        return FileResponse(index_html)
