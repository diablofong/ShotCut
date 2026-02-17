# ShotCut

籃球比賽影片標記與片段擷取工具。上傳比賽影片，透過音訊分析自動偵測關鍵時間點，快速標記分類並自動剪輯出精華片段。

## 功能特色

- **影片上傳** — 支援本機上傳與 YouTube 連結匯入（yt-dlp）
- **音訊自動偵測** — 利用 librosa 分析哨音、歡呼聲等音訊特徵，自動產生候選時間點
- **快速標記與分類** — 將時間點標記為進攻、防守、精彩、失誤等類別，並可標註球員編號
- **自動片段擷取** — 透過 FFmpeg 依據標記自動切出影片片段
- **個人精華剪輯** — 依球員或標籤自動合併產出個人精華影片
- **分享連結** — 產生分享連結供教練與家長觀看

## 技術架構

| 層級 | 技術 |
|------|------|
| 前端 | React 19 + TypeScript + Vite + Tailwind CSS + Video.js |
| 後端 | Python 3.11 + FastAPI + SQLAlchemy (async) |
| 資料庫 | MariaDB 11 |
| 影片處理 | FFmpeg (ffmpeg-python) |
| 音訊分析 | librosa + scipy |
| 影片下載 | yt-dlp |
| 部署 | Docker + Docker Compose |

## 快速開始

### 環境需求

- [Docker](https://www.docker.com/) 與 Docker Compose
- 或手動安裝：Node.js 20+、Python 3.11+、FFmpeg、MariaDB

### 使用 Docker（推薦）

```bash
# 複製環境變數範本
cp .env.example .env

# 依需求修改 .env 中的密碼與設定

# 啟動服務
docker compose up -d
```

啟動後開啟瀏覽器前往 `http://localhost:8000`。

### 本機開發

**後端：**

```bash
# 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安裝依賴
pip install -r backend/requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 中的 DATABASE_URL 指向你的 MariaDB

# 執行資料庫遷移
alembic upgrade head

# 啟動開發伺服器
uvicorn backend.main:app --reload
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

前端開發伺服器預設在 `http://localhost:5173`，後端 API 在 `http://localhost:8000`。

## 專案結構

```
ShotCut/
├── backend/            # FastAPI 後端
│   ├── models/         # SQLAlchemy 資料模型
│   ├── routers/        # API 路由
│   ├── services/       # 業務邏輯
│   └── main.py         # 應用程式進入點
├── frontend/           # React 前端
│   └── src/
├── alembic/            # 資料庫遷移
├── uploads/            # 上傳影片存放（git 忽略）
├── clips/              # 擷取片段存放（git 忽略）
├── docker-compose.yml  # 生產環境部署
├── docker-compose.dev.yml  # 開發環境
└── Dockerfile
```

## API 端點

所有 API 端點皆在 `/api` 前綴下：

- `/api/videos` — 影片管理
- `/api/analysis` — 音訊分析
- `/api/marks` — 時間標記
- `/api/clips` — 片段擷取
- `/api/highlights` — 精華剪輯
- `/api/shares` — 分享連結

## 授權條款

本專案採用 [MIT License](LICENSE) 授權。
