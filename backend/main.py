import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.db.database import engine
from backend.routers import auth, users, videos, analysis, marks, clips, highlights, shares


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="ShotCut API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(marks.router, prefix="/api")
app.include_router(clips.router, prefix="/api")
app.include_router(highlights.router, prefix="/api")
app.include_router(shares.router, prefix="/api")

# 生產環境掛載前端靜態檔案
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    # 靜態資源（JS/CSS/圖片）
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    index_html = os.path.join(frontend_dist, "index.html")

    # favicon 等根目錄靜態檔
    @app.get("/favicon.svg")
    async def favicon():
        return FileResponse(os.path.join(frontend_dist, "favicon.svg"))

    # SPA catch-all：所有非 /api 路徑返回 index.html
    @app.get("/{full_path:path}")
    async def spa_fallback(request: Request, full_path: str):
        # 如果請求的是實際存在的靜態檔，直接返回
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(index_html)
