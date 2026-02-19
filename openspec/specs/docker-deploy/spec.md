## ADDED Requirements

### Requirement: 健康檢查端點
系統 SHALL 提供 `GET /health` 端點，不需認證即可存取，回傳 `{"status": "ok"}`。

#### Scenario: 健康檢查成功
- **WHEN** Docker 或監控系統請求 `GET /health`
- **THEN** 系統回傳 200 OK 與 `{"status": "ok"}`，不需 JWT token

### Requirement: Docker Compose 服務編排
系統 SHALL 使用 docker-compose.yml 定義並編排所有服務（應用程式、MariaDB）。

#### Scenario: 一鍵啟動所有服務
- **WHEN** 使用者執行 `docker-compose up`
- **THEN** 所有服務啟動，應用程式可透過瀏覽器存取

#### Scenario: 服務啟動順序
- **WHEN** docker-compose 啟動服務
- **THEN** MariaDB 先啟動並通過 healthcheck 後，應用程式服務才啟動

### Requirement: 應用程式容器
系統 SHALL 提供 Dockerfile 建置應用程式映像，包含 Python 後端、前端靜態檔案、FFmpeg 與 yt-dlp。SPA catch-all 路由 MUST 驗證請求路徑不超出前端靜態檔案目錄，防止路徑遍歷攻擊。

#### Scenario: 建置應用程式映像
- **WHEN** 執行 Docker 映像建置
- **THEN** 映像包含 Python 環境、所有 pip 依賴、Node.js 建置的前端 dist、FFmpeg、yt-dlp、Node.js runtime（yt-dlp YouTube 解析所需）

#### Scenario: 生產環境運行
- **WHEN** 應用程式容器啟動
- **THEN** Uvicorn 啟動 FastAPI 應用，提供 API 服務並掛載前端靜態檔案

#### Scenario: SPA fallback 路徑遍歷防護
- **WHEN** 請求路徑包含 `..` 或其他路徑遍歷嘗試
- **THEN** 系統 SHALL 忽略該路徑並返回 index.html，不得回傳前端目錄外的任何檔案

### Requirement: MariaDB 容器
系統 SHALL 使用 MariaDB 官方映像，支援資料持久化與自動初始化。

#### Scenario: 首次啟動資料庫
- **WHEN** MariaDB 容器首次啟動
- **THEN** 使用環境變數建立資料庫與使用者，Alembic migration 自動建立所有資料表

#### Scenario: 資料持久化
- **WHEN** 容器重啟
- **THEN** 資料庫資料透過 Docker volume 保留，不會遺失

### Requirement: 環境變數配置
系統 SHALL 透過 .env 檔案管理所有環境變數，並提供 .env.example 範本。docker-compose.yml 中的環境變數 MUST NOT 包含硬編碼的密碼 fallback。.env.example MUST 包含 CORS_ORIGINS 和 MAX_UPLOAD_SIZE_MB 的說明。

#### Scenario: 使用範本配置
- **WHEN** 使用者複製 .env.example 為 .env 並填入設定
- **THEN** docker-compose 讀取 .env 中的資料庫密碼、連接埠、管理員帳密、JWT 過期時間、CORS 來源、上傳大小限制等設定

#### Scenario: 必要環境變數未設定
- **WHEN** docker-compose 啟動時缺少必要環境變數（SECRET_KEY、DATABASE_URL）
- **THEN** 應用程式 SHALL 啟動失敗並輸出明確的錯誤訊息

### Requirement: 影片檔案掛載
系統 SHALL 將 uploads/ 與 clips/ 目錄掛載為 Docker volume，確保影片檔案持久化。

#### Scenario: 影片檔案持久化
- **WHEN** 容器重啟或重建
- **THEN** uploads/、clips/、highlights/ 中的影片檔案透過 bind mount（./data/）保留

### Requirement: 開發模式支援
系統 SHALL 支援開發模式，原始碼掛載至容器內並支援熱重載。

#### Scenario: 後端熱重載
- **WHEN** 開發者修改 Python 原始碼
- **THEN** Uvicorn 自動偵測變更並重新載入

#### Scenario: 前端獨立開發
- **WHEN** 開發者啟動前端開發伺服器
- **THEN** Vite dev server 啟動，支援 HMR 熱更新，API 請求代理至後端容器
