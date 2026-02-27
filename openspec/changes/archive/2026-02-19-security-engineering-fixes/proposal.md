## Why

ShotCut 專案經過全面安全審查後，發現 15 個關鍵的安全漏洞和工程缺陷，包含敏感資訊洩露（.env 已簽入 Git）、Token 安全問題（localStorage 儲存導致 XSS 風險）、容器安全風險（root 用戶運行）、命令注入漏洞（FFmpeg 路徑未驗證）等。這些問題若不立即修復，將嚴重威脅用戶資料安全和系統穩定性。

## What Changes

**極高優先級（Critical - 5 項）**：
- 從 Git 歷史中完全移除已洩露的 `.env` 檔案
- 將前端 Token 儲存從 localStorage 改為 HttpOnly Cookie 或內存
- 移除所有 URL 參數中的 Token 傳遞（影片縮圖、下載、WebSocket）
- Cookie Secure Flag 自動偵測（IS_PRODUCTION=true 或 X-Forwarded-Proto: https，支援反向代理場景）
- 容器改為非 root 用戶運行

**高優先級（High - 5 項）**：
- FFmpeg 命令注入防護（檔案路徑驗證與轉義）
- 檔案上傳魔數驗證（防止偽造副檔名）
- 移除資料庫埠暴露到主機（docker-compose.yml）
- 限制 CORS 設定（明確指定允許的 methods 和 headers）
- CI/CD 加入安全掃描（秘密掃描、依賴漏洞掃描、容器映像掃描）

**中優先級（Medium - 5 項）**：
- 更新前端依賴修復 npm 漏洞（minimatch、ajv）
- 新增 `.dockerignore` 防止敏感檔案進入映像
- Secret Key 強度驗證（啟動時檢查）
- 檔案名稱清理防止路徑遍歷攻擊
- 資料庫連接池配置防止資源耗盡

## Capabilities

### New Capabilities

- `input-validation`: 檔案上傳內容驗證（魔數檢查）、檔案名稱清理、路徑遍歷防護
- `dependency-security`: 依賴漏洞管理、CI/CD 安全掃描（pip-audit、npm audit、容器掃描、秘密掃描）

### Modified Capabilities

- `user-auth`: Token 儲存機制改變（從 localStorage 改為 HttpOnly Cookie/內存）、Cookie Secure Flag 啟用、移除 Query Parameter 認證
- `docker-deploy`: 容器非 root 用戶運行、.dockerignore 檔案、資料庫埠暴露移除
- `config-management`: Secret Key 強度驗證、環境變數安全性強化、.env 檔案從 Git 移除
- `ci-cd`: 加入安全掃描步驟（秘密掃描、依賴漏洞、SAST）
- `video-ingest`: 檔案上傳加入魔數驗證、檔案名稱清理
- `clip-extraction`: FFmpeg 路徑驗證防止命令注入
- `highlight-generation`: FFmpeg concat 檔案路徑轉義
- `frontend-app`: 移除 URL 中 Token 參數、改用 Authorization Header 或 Cookie
- `rate-limiting`: 為敏感操作（修改密碼、刪除用戶）加入限流

## Impact

**受影響的後端檔案（13 個）**：
- `backend/routers/auth.py` - Cookie Secure Flag
- `backend/routers/videos.py` - 移除 Query Token、加入路徑驗證
- `backend/routers/clips.py` - 移除 Query Token
- `backend/routers/highlights.py` - 移除 Query Token
- `backend/services/video_service.py` - 魔數驗證、檔案名清理
- `backend/services/clip_service.py` - FFmpeg 路徑驗證
- `backend/services/highlight_service.py` - FFmpeg 路徑轉義
- `backend/config.py` - Secret Key 驗證、is_production 設定
- `backend/db/database.py` - 連接池配置
- `backend/main.py` - CORS 限制

**受影響的前端檔案（7 個）**：
- `frontend/src/contexts/AuthContext.tsx` - 移除 localStorage Token
- `frontend/src/services/api.ts` - 移除 localStorage、改 WebSocket 認證
- `frontend/src/pages/VideosPage.tsx` - 移除 URL Token
- `frontend/src/pages/VideoDetailPage.tsx` - 移除 URL Token
- `frontend/src/pages/ClipsPage.tsx` - 移除 URL Token
- `frontend/src/pages/HighlightsPage.tsx` - 移除 URL Token
- `frontend/package.json` - 更新依賴

**受影響的部署與 CI/CD 檔案（5 個）**：
- `Dockerfile` - 非 root 用戶
- `docker-compose.yml` - 移除資料庫埠暴露
- `.dockerignore` - 新增檔案
- `.github/workflows/backend-ci.yml` - 安全掃描
- `.github/workflows/frontend-ci.yml` - 安全掃描

**受影響的 API**：
- 所有需要認證的端點（改用 Cookie/Header 而非 Query Parameter）
- WebSocket 連接認證方式改變

**受影響的依賴**：
- 新增：`python-magic` 或 `filetype`（魔數檢查）
- 新增：`pip-audit`、`bandit`（CI 安全掃描）
- 更新：前端 `minimatch`、`ajv` 套件

**資料庫與資料**：
- 需要清除 Git 歷史中的 `.env` 檔案
- 資料庫連接池參數調整

**破壞性變更**：
- **BREAKING**: 前端用戶需要重新登入（Token 儲存方式改變）
- **BREAKING**: 直接使用 Query Parameter Token 的外部整合將失效
