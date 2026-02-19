## 1. 清除死依賴

- [x] 1.1 從 `backend/requirements.txt` 移除 `librosa==0.10.2` 與 `scipy==1.14.1`
- [x] 1.2 確認後端所有 `.py` 檔案無 `import librosa` 或 `import scipy`（grep 驗證）
- [x] 1.3 重建 Docker image，確認建構成功（已完成，移除 libsndfile1 後重建成功）

## 2. 集中化設定管理（pydantic-settings）

- [x] 2.1 新增 `pydantic-settings` 至 `backend/requirements.txt`
- [x] 2.2 建立 `backend/config.py`：定義 `Settings(BaseSettings)` 類別，包含所有環境變數欄位與型別，`@lru_cache` 快取 `get_settings()`
- [x] 2.3 更新 `backend/db/database.py`：以 `get_settings().database_url` 取代 `os.getenv("DATABASE_URL")`
- [x] 2.4 更新 `backend/auth/security.py`：以 `get_settings().secret_key` 取代 `os.getenv("SECRET_KEY")`
- [x] 2.5 更新 `backend/main.py`：以 `get_settings().cors_origins` 取代 `os.getenv("CORS_ORIGINS")`
- [x] 2.6 更新 `backend/services/video_service.py`、`clip_service.py`、`highlight_service.py`：以 settings 取代所有 `os.getenv()` 呼叫
- [x] 2.7 `backend/utils/streaming.py` 確認無 `os.getenv()` 呼叫，路徑由 router 層傳入，無需修改

## 3. 結構化日誌 + 健康檢查端點

- [x] 3.1 在 `backend/main.py` 新增 `JsonLoggingMiddleware`：每次請求產生含 `request_id`、`method`、`path`、`status_code`、`duration_ms` 的 JSON 日誌
- [x] 3.2 使用 `contextvars.ContextVar` 儲存 `request_id`，讓 service 層日誌也能取得
- [x] 3.3 設定 Python logging root handler 輸出 JSON 格式（自訂 `JsonFormatter`）
- [x] 3.4 新增 `GET /api/health` 路由（不需認證）：執行 `SELECT 1` 驗證 DB 連線，回傳 `{"status": "healthy"/"unhealthy", "database": "ok"/"error", "timestamp": "..."}`
- [x] 3.5 將 `/api/health` 路由加入 `backend/main.py` 並排除於認證中介軟體外

## 4. Rate Limiting

- [x] 4.1 新增 `slowapi` 至 `backend/requirements.txt`
- [x] 4.2 在 `backend/main.py` 初始化 `Limiter`（`key_func=get_remote_address`）並掛載 `SlowAPIMiddleware`
- [x] 4.3 在 `backend/routers/auth.py` 對 `POST /api/auth/login` 加上 `@limiter.limit("5/minute")` 裝飾器
- [x] 4.4 在 `backend/routers/videos.py` 對 `POST /api/videos/upload` 加上 `@limiter.limit("10/hour")`
- [x] 4.5 在 `backend/routers/videos.py` 對 `POST /api/videos/download` 加上 `@limiter.limit("10/hour")`
- [x] 4.6 新增全局 `RateLimitExceeded` exception handler，回傳 `{"detail": "請求過於頻繁，請稍後再試"}` 與 `Retry-After` header

## 5. Refresh Token 機制

- [x] 5.1 建立 Alembic migration：新增 `refresh_tokens` 表（欄位：`id`、`user_id`、`token_hash`（sha256）、`expires_at`、`created_at`、`revoked`）
- [x] 5.2 在 `backend/models/` 新增 `refresh_token.py`：定義 `RefreshToken` ORM model
- [x] 5.3 更新 `backend/auth/security.py`：新增 `create_refresh_token()`（產生隨機 token、hash 後存 DB）、`verify_refresh_token()`（查 DB 驗證）
- [x] 5.4 更新 `backend/routers/auth.py` 的登入端點：登入成功後產生 refresh_token 並以 httpOnly Cookie 回傳（`Set-Cookie: refresh_token=...; HttpOnly; SameSite=Lax; Max-Age=604800`）
- [x] 5.5 在 `backend/routers/auth.py` 新增 `POST /api/auth/refresh` 端點：讀取 Cookie 中的 refresh_token、驗證、發行新 access_token
- [x] 5.6 在 `backend/routers/auth.py` 新增 `POST /api/auth/logout` 端點：將 refresh_token 標記為 revoked，清除 Cookie
- [x] 5.7 更新 `backend/config.py` Settings：新增 `jwt_access_expire_minutes: int = 15`（原 `JWT_EXPIRE_MINUTES` 重命名）與 `jwt_refresh_expire_days: int = 7`
- [x] 5.8 更新前端 `frontend/src/services/api.ts`：在 axios response interceptor 中，收到 401 時自動 POST `/api/auth/refresh`；refresh 成功則重試，失敗則重導向登入頁

## 6. 後端測試基礎架構

- [x] 6.1 新增測試依賴至 `backend/requirements.txt`：`pytest`、`pytest-asyncio`、`httpx`、`aiosqlite`
- [x] 6.2 建立 `backend/tests/__init__.py`
- [x] 6.3 建立 `backend/tests/conftest.py`：定義 `async_engine`（SQLite）、`async_session`、`client`（AsyncClient + override `get_db`）、`admin_token`、`user_token` fixtures
- [x] 6.4 建立 `backend/pytest.ini`（或 `pyproject.toml` 的 `[tool.pytest.ini_options]`）：設定 `asyncio_mode = "auto"`
- [x] 6.5 建立 `backend/tests/test_auth.py`：測試登入成功、登入失敗、token refresh、logout
- [x] 6.6 建立 `backend/tests/test_videos.py`：測試影片列表（認證/未認證）、影片存取權限
- [x] 6.7 建立 `backend/tests/test_marks.py`：測試建立標記、他人無法刪除標記
- [x] 6.8 建立 `backend/tests/test_shares.py`：測試公開存取分享連結、過期分享連結返回 410
- [x] 6.9 建立 `backend/tests/test_health.py`：測試 `/api/health` 端點回傳 200 且不需認證
- [x] 6.10 在 Docker 容器內執行 `pytest backend/tests/`，23/23 全部通過

## 7. GitHub Actions CI/CD

- [x] 7.1 建立 `.github/workflows/` 目錄
- [x] 7.2 建立 `.github/workflows/backend-ci.yml`：triggers（push + pull_request）、setup-python（3.12）、install deps（含 ruff）、執行 `ruff check backend/`、執行 `pytest backend/tests/`
- [x] 7.3 建立 `.github/workflows/frontend-ci.yml`：triggers（push + pull_request）、setup-node（22）、`npm ci`、執行 `npm run lint`、執行 `npx tsc --noEmit`
- [ ] 7.4 push 至 GitHub 確認兩個 workflow 均成功執行（需手動執行）

## 8. WebSocket 下載進度推送

- [x] 8.1 在 `backend/` 建立 `websocket_manager.py`：`ConnectionManager` 類別，含 `connect(video_id, ws)`、`disconnect(video_id, ws)`、`broadcast(video_id, data)` 方法
- [x] 8.2 在 `backend/routers/videos.py` 新增 `WS /api/videos/{video_id}/ws/progress` 端點：支援 `?token=` query 認證，接受連線並監聽直到斷線
- [x] 8.3 更新 `backend/services/video_service.py` 下載進度 callback：在進度更新時呼叫 `manager.broadcast(video_id, {...})`（透過 `asyncio.run_coroutine_threadsafe` 跨事件迴圈廣播）
- [x] 8.4 更新前端 `frontend/src/pages/VideosPage.tsx`：移除 `setInterval` polling，改以 `WebSocket` 連線 `/api/videos/{id}/ws/progress?token=<access_token>` 接收進度
- [x] 8.5 實作前端 WebSocket 連線失敗降級邏輯：WebSocket 建立失敗時改為每 3 秒 polling
- [ ] 8.6 測試下載進度即時更新正確顯示於 UI（需手動驗證）
