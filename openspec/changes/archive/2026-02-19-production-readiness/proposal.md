## Why

ShotCut 目前功能完整但缺乏生產環境所需的基礎建設：測試覆蓋率為零、無 CI/CD 守門機制、無速率限制、日誌不可追蹤、設定分散、認證機制不完善。為提升系統可靠性、安全性與維護性，現在進行系統性補強。

## What Changes

- **移除死依賴**：從 `requirements.txt` 移除 `librosa` 與 `scipy`（音訊分析功能已移除，這兩個依賴增加 Docker image ~300MB 且帶來不必要的攻擊面）
- **新增後端測試基礎架構**：引入 `pytest` + `pytest-asyncio` + `httpx`，涵蓋 API 端點的整合測試（認證、影片、標記、片段、精華、分享）
- **新增 GitHub Actions CI/CD**：每次 push / PR 自動執行後端 lint（ruff）+ 測試（pytest）+ 前端 lint（eslint）+ 型別檢查（tsc）
- **新增 Rate Limiting**：使用 `slowapi` 對登入、上傳、下載等高風險端點加上頻率限制
- **新增可觀測性**：結構化日誌（JSON 格式含 request_id、路徑、耗時）+ `/api/health` 深度健康檢查端點
- **集中化設定管理**：使用 `pydantic-settings` 取代散落各處的 `os.getenv()`，提供型別安全與啟動驗證
- **新增 Refresh Token 機制**：引入 Access Token（短效）+ Refresh Token（長效）雙 token 策略，新增 `/api/auth/refresh` 端點
- **WebSocket 推送下載進度**：以 WebSocket 取代前端每秒 polling `/videos/{id}/status`，降低伺服器負載並提升即時性

## Capabilities

### New Capabilities
- `test-infrastructure`: 後端整合測試架構（pytest + pytest-asyncio + httpx），涵蓋所有主要 API 端點
- `ci-cd`: GitHub Actions 工作流程，自動化 lint、型別檢查與測試
- `rate-limiting`: API 速率限制，保護登入、上傳、下載等高風險端點
- `observability`: 結構化 JSON 日誌（含 request_id）+ `/api/health` 深度健康檢查端點
- `config-management`: 使用 `pydantic-settings` 集中管理所有環境變數設定，啟動時驗證必填項目
- `websocket-progress`: WebSocket 即時推送影片下載進度，取代輪詢機制

### Modified Capabilities
- `user-auth`: 新增 Refresh Token 流程，`/api/auth/login` 回傳 access_token + refresh_token，新增 `/api/auth/refresh` 端點；前端改以 httpOnly Cookie 儲存 refresh_token（access_token 仍用 localStorage，後續可進一步強化）

## Impact

- **後端依賴**：`requirements.txt` 移除 librosa、scipy；新增 slowapi、pydantic-settings
- **後端程式碼**：`backend/main.py`（middleware 注入）、`backend/auth/`（refresh token 邏輯）、`backend/db/database.py`（設定集中化）、所有 routers（rate limiting 裝飾器）
- **前端程式碼**：`frontend/src/services/api.ts`（WebSocket 邏輯、token refresh interceptor）、`frontend/src/pages/VideoDetailPage.tsx`（移除 polling）
- **新增目錄**：`backend/tests/`、`.github/workflows/`
- **Docker**：image 大小顯著縮小（移除音訊分析依賴），entrypoint 無需異動
- **資料庫**：新增 refresh_tokens 表（需新增 Alembic migration）
