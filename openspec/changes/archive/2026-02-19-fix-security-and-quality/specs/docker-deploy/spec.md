## MODIFIED Requirements

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

### Requirement: 環境變數配置
系統 SHALL 透過 .env 檔案管理所有環境變數，並提供 .env.example 範本。docker-compose.yml 中的環境變數 MUST NOT 包含硬編碼的密碼 fallback。.env.example MUST 包含 CORS_ORIGINS 和 MAX_UPLOAD_SIZE_MB 的說明。

#### Scenario: 使用範本配置
- **WHEN** 使用者複製 .env.example 為 .env 並填入設定
- **THEN** docker-compose 讀取 .env 中的資料庫密碼、連接埠、管理員帳密、JWT 過期時間、CORS 來源、上傳大小限制等設定

#### Scenario: 必要環境變數未設定
- **WHEN** docker-compose 啟動時缺少必要環境變數（SECRET_KEY、DATABASE_URL）
- **THEN** 應用程式 SHALL 啟動失敗並輸出明確的錯誤訊息
