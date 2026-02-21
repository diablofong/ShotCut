# ShotCut

籃球比賽影片標記與片段擷取工具。上傳比賽影片，快速標記分類並自動剪輯出精華片段，分享給教練與家長。

> English documentation: [README.md](README.md)

## 畫面預覽

[![ShotCut Demo](https://img.youtube.com/vi/4Bdpn3-4Xuk/maxresdefault.jpg)](https://youtu.be/4Bdpn3-4Xuk)

## 功能特色

- **影片管理** — 支援本機上傳與 YouTube 連結匯入（yt-dlp），表格式管理介面含搜尋與縮圖預覽
- **下載進度即時推送** — WebSocket 即時顯示 YouTube 下載進度（速度/剩餘時間），斷線自動降級為 polling
- **軌道式快速標記** — 播放中按數字鍵 1-3 即時標記進攻/防守/失誤，時間軸色塊拖曳微調
- **球員標註** — 支援標註球員編號與姓名（如「7 林書豪, 11 王大明」）
- **自動片段擷取** — 透過 FFmpeg 依據標記自動切出影片片段
- **個人精華剪輯** — 依球員或分類自動合併產出個人精華影片
- **分享連結** — 產生分享連結（支援 24h/7d/30d/永久有效期）供教練與家長觀看
- **播放速度控制** — 支援 0.25x ~ 2x 播放速度（慢動作回放/快速瀏覽）
- **安全認證** — JWT Access Token（15 分鐘）+ Refresh Token（7 天，httpOnly Cookie）、角色權限（管理員/一般使用者）、資料隔離

## 技術架構

| 層級 | 技術 |
|------|------|
| 前端 | React 19 + TypeScript + Vite + Tailwind CSS + Video.js |
| 後端 | Python 3.11 + FastAPI + SQLAlchemy (async) |
| 資料庫 | MariaDB 11 |
| 影片處理 | FFmpeg |
| 影片下載 | yt-dlp |
| 即時通訊 | WebSocket（FastAPI 原生） |
| 安全防護 | slowapi rate limiting、bcrypt 密碼加密 |
| 部署 | Docker + Docker Compose |

## 快速開始

### 環境需求

- [Docker](https://www.docker.com/) 與 Docker Compose

### 使用 Docker（推薦）

```bash
# 複製環境變數範本
cp .env.example .env

# 依需求修改 .env 中的密碼與設定
# 必須修改：SECRET_KEY、ADMIN_PASSWORD、資料庫密碼

# 啟動服務
docker compose up -d
```

啟動後開啟瀏覽器前往 `http://localhost:8000`。

### 本機開發

**後端：**

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r backend/requirements.txt

cp .env.example .env
# 編輯 .env 中的 DATABASE_URL 指向你的 MariaDB

alembic upgrade head

uvicorn backend.main:app --reload
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

前端開發伺服器：`http://localhost:5173`　後端 API：`http://localhost:8000`

## 安全最佳實踐

ShotCut 實作多層安全機制保護您的資料：

### 生產環境部署檢查清單

部署到生產環境前，請確認：

1. **環境變數設定**
   - 產生強密鑰 `SECRET_KEY`（≥32 字符）：`python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - 使用強密碼（≥16 字符含大小寫數字特殊符號）作為資料庫憑證
   - 修改 `ADMIN_PASSWORD` 預設值
   - `IS_PRODUCTION=true` 強制啟用 Cookie Secure Flag，僅在直接終止 HTTPS（不經反向代理）時才需設定

2. **HTTPS 與 CORS**
   - 透過反向代理（nginx/Caddy）部署並配置有效的 SSL/TLS 憑證
   - **Cookie Secure Flag 自動偵測**：反向代理設定 `X-Forwarded-Proto: https` 時自動啟用，無需手動設定 `IS_PRODUCTION=true`
   - 設定 `CORS_ORIGINS` 僅包含生產網域（如 `https://shotcut.example.com`）

3. **容器安全**
   - 應用程式在 Docker 容器內以非 root 用戶（`shotcut`）執行
   - 資料庫埠（3306）未對外暴露，僅可透過 Docker 內部網路存取
   - 敏感檔案（`.env`、`.git`、`data/`）透過 `.dockerignore` 排除在 Docker 映像外

4. **Token 安全**
   - Access Token 儲存於記憶體（非 localStorage），關閉頁面自動清除
   - Refresh Token 儲存於 httpOnly Cookie，免疫 XSS 攻擊
   - URL 查詢參數不含 Token，防止在日誌與瀏覽器歷史記錄中洩漏

5. **檔案上傳安全**
   - 魔術數字驗證防止偽造副檔名（如 `.exe` 改名為 `.mp4`）
   - 檔名清理移除路徑遍歷字符（`../`、`..\\`）
   - FFmpeg 命令注入防護：路徑驗證與 shell 轉義

6. **CI/CD 安全掃描**
   - 自動化依賴審計：`pip-audit`（Python）與 `npm audit`（Node.js）
   - 靜態分析：Bandit（Python SAST）
   - 秘密掃描：TruffleHog

### 安全監控

部署後：
- 監控應用程式日誌中的認證失敗與可疑活動
- 定期更新依賴套件：`docker compose build --pull`
- 訂閱 FastAPI、React、MariaDB 的安全公告

### 從舊版本升級

**破壞性變更：** 如果您從安全修復前的版本（commit `e371ae7` 之前）升級：
- 所有使用者必須重新登入（Token 儲存機制變更：localStorage → 記憶體）
- Refresh Token 現為 httpOnly Cookie，請更新任何自訂 API 客戶端

## 執行測試

測試使用 SQLite in-memory，不需要額外的 MariaDB 實例：

```bash
# 在 Docker 容器中執行（推薦，不需要本機 Python 環境）
docker run --rm \
  --entrypoint python \
  -e DATABASE_URL="sqlite+aiosqlite:///:memory:" \
  -e SECRET_KEY="test-secret-key" \
  shotcut-app \
  -m pytest backend/tests/ -v --cov=backend
```

**目前狀態：23/23 測試通過 — 覆蓋率 56%**（門檻：50%）

## 環境變數

| 變數名稱 | 必填 | 預設值 | 說明 |
|---------|------|--------|------|
| `DATABASE_URL` | ✅ | — | MariaDB 連線字串 |
| `SECRET_KEY` | ✅ | — | JWT 簽署密鑰（≥32 字符，使用 `.env.example` 中的生成器） |
| `IS_PRODUCTION` | | `false` | 強制啟用 Cookie Secure Flag；反向代理設定 `X-Forwarded-Proto: https` 時自動啟用 |
| `ADMIN_USERNAME` | | `admin` | 初始管理員帳號 |
| `ADMIN_PASSWORD` | | `admin1234` | 初始管理員密碼（**務必修改**） |
| `JWT_ACCESS_EXPIRE_MINUTES` | | `15` | Access Token 有效期（分鐘） |
| `JWT_REFRESH_EXPIRE_DAYS` | | `7` | Refresh Token 有效期（天） |
| `CORS_ORIGINS` | | `""` | 允許的 CORS 來源（逗號分隔） |
| `MAX_UPLOAD_SIZE_MB` | | `2048` | 上傳檔案大小上限（MB） |
| `FFMPEG_TIMEOUT` | | `300` | FFmpeg 處理超時（秒） |
| `APP_PORT` | | `8000` | 對外開放的連接埠 |

## 專案結構

```
ShotCut/
├── backend/                # FastAPI 後端
│   ├── auth/               # JWT 認證與權限控制
│   ├── db/                 # 資料庫連線設定
│   ├── models/             # SQLAlchemy 資料模型
│   ├── routers/            # API 路由
│   ├── services/           # 業務邏輯
│   ├── tests/              # 整合測試（pytest + httpx）
│   ├── config.py           # 集中化設定管理（pydantic-settings）
│   ├── limiter.py          # Rate limiting（slowapi）
│   ├── websocket_manager.py# WebSocket 連線管理
│   └── main.py             # 應用程式進入點
├── frontend/               # React 前端
│   └── src/
│       ├── components/     # 共用元件
│       ├── contexts/       # React Context（認證等）
│       ├── hooks/          # 自訂 Hooks
│       ├── pages/          # 頁面元件
│       └── services/       # API 服務層
├── alembic/                # 資料庫遷移
├── .github/workflows/      # GitHub Actions CI/CD
│   ├── backend-ci.yml      # 後端 lint + 測試
│   └── frontend-ci.yml     # 前端 lint + 型別檢查
├── data/                   # 運行時資料（git 忽略）
│   ├── uploads/
│   ├── clips/
│   ├── highlights/
│   ├── thumbnails/
│   └── db/
├── openspec/               # OpenSpec 規格文件
├── docker-compose.yml      # 生產環境部署
├── docker-compose.dev.yml  # 開發環境
└── Dockerfile
```

## API 端點

所有端點皆在 `/api` 前綴下：

| 端點 | 說明 |
|------|------|
| `GET /api/health` | 健康檢查（無需認證） |
| `POST /api/auth/login` | 登入 — 回傳 Access Token + 設定 Refresh Token Cookie |
| `POST /api/auth/refresh` | 使用 Refresh Token 換取新 Access Token |
| `POST /api/auth/logout` | 撤銷 Refresh Token 並清除 Cookie |
| `GET /api/auth/me` | 當前使用者資訊 |
| `GET /api/videos` | 影片列表 |
| `POST /api/videos/upload` | 上傳影片檔案 |
| `POST /api/videos/download` | 從 YouTube URL 匯入 |
| `WS /api/videos/{id}/ws/progress` | 下載進度即時推送（WebSocket） |
| `GET /api/marks` | 取得影片標記列表 |
| `POST /api/clips` | 從標記擷取片段 |
| `POST /api/highlights/generate` | 產生精華剪輯 |
| `POST /api/shares` | 建立分享連結 |

完整互動式 API 文件：`http://localhost:8000/docs`（Swagger UI）

## 授權條款

[MIT License](LICENSE)
