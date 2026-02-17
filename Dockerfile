# ---- 前端建置階段 ----
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- 後端運行階段 ----
FROM python:3.11-slim

# 安裝系統依賴：FFmpeg + 音訊處理所需函式庫 + Node.js（yt-dlp YouTube 解析需要 JS runtime）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# 安裝 yt-dlp
RUN pip install --no-cache-dir yt-dlp

WORKDIR /app

# 安裝 Python 依賴
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 複製後端程式碼
COPY backend/ ./backend/
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY entrypoint.sh ./

# 複製前端建置產出
COPY --from=frontend-build /frontend/dist ./frontend/dist

# 建立影片儲存目錄
RUN mkdir -p /app/uploads /app/clips /app/highlights /app/thumbnails

# 修正 Windows CRLF 換行符並設定執行權限
RUN sed -i 's/\r$//' ./entrypoint.sh && chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
