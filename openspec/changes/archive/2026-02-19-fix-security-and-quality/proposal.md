## Why

專案即將公開發佈，經過全面安全審查發現多項嚴重安全漏洞與程式碼品質問題。包括 SPA fallback 路徑遍歷、精華剪輯端點缺少權限驗證（IDOR）、硬編碼密碼/密鑰作為 fallback 預設值、檔案上傳無大小限制、CORS 全開、Range header 未驗證、時區處理不一致、背景任務資源洩漏，以及前端 polling 無限循環。這些問題必須在公開前修復。

## What Changes

### 安全漏洞修復
- 修復 SPA catch-all 路由的路徑遍歷漏洞（驗證 `file_path` 在 `frontend_dist` 目錄內）
- **BREAKING**: 精華剪輯的 stream/download/thumbnail 端點加入擁有者權限驗證（原本任何已登入使用者可存取所有精華剪輯）
- **BREAKING**: 移除所有環境變數的硬編碼 fallback 預設值（`SECRET_KEY`、`DATABASE_URL`、`ADMIN_PASSWORD`），未設定時啟動直接報錯
- 加入檔案上傳大小限制（預設 2GB）
- CORS 設定從 `allow_origins=["*"]` 改為從環境變數讀取的明確 origin 清單
- 所有串流端點加入 Range header 驗證（`start >= 0`、`start <= end`、`end < file_size`）

### 程式碼品質修復
- 統一時區處理：`datetime.utcnow()` → `datetime.now(timezone.utc)`
- 背景下載函式加入 `try-finally` 確保 `engine.dispose()` 執行
- 移除 yt-dlp 的 `remote_components` 和 `js_runtimes` 不安全設定
- 前端 `VideosPage` polling 修復依賴陣列，避免無限循環

## Capabilities

### New Capabilities

（無新增 capability）

### Modified Capabilities
- `user-auth`: 移除硬編碼的 SECRET_KEY/DB 密碼 fallback，環境變數未設定時啟動失敗；CORS 來源從環境變數讀取
- `video-ingest`: 上傳端點加入檔案大小上限驗證（預設 2GB）；移除 yt-dlp 不安全的遠端元件設定；背景下載資源洩漏修復
- `highlight-generation`: stream、download、thumbnail 端點加入擁有者權限驗證，非擁有者回傳 403
- `sharing`: 修正 `datetime.utcnow()` 為 timezone-aware 的 `datetime.now(timezone.utc)`
- `frontend-app`: 修復 VideosPage polling 的 useEffect 依賴陣列導致的無限循環
- `docker-deploy`: SPA fallback 路徑遍歷修復；CORS 環境變數化
- `clip-extraction`: 串流端點 Range header 輸入驗證

## Impact

- **後端**：`backend/main.py`、`backend/auth/security.py`、`backend/db/database.py`、`backend/routers/videos.py`、`backend/routers/highlights.py`、`backend/routers/shares.py`、`backend/routers/clips.py`、`backend/services/video_service.py`、`backend/scripts/seed_admin.py`、`alembic/env.py`
- **前端**：`frontend/src/pages/VideosPage.tsx`
- **部署**：`.env.example`、`docker-compose.yml`
- **BREAKING 變更**：精華剪輯端點權限收緊（原本可跨使用者存取）、移除 fallback 預設值（部署時必須設定所有環境變數）
