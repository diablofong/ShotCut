## Context

ShotCut 是一個 FastAPI + React 的籃球影片標記工具，目前功能完整但缺乏生產環境基礎建設。本 design 涵蓋 8 項改善的技術決策，範圍橫跨後端（Python）、前端（TypeScript）、DevOps（GitHub Actions）、資料庫（Alembic migration）。

現有技術棧：FastAPI 0.115、SQLAlchemy 2.0 async、asyncmy（MariaDB）、pydantic v2、python-jose（JWT）、React 19、Vite、Tailwind。

## Goals / Non-Goals

**Goals:**
- 測試覆蓋率從 0% 提升至主要 API 端點均有整合測試
- CI/CD 守門：每次 push 自動執行 lint + 測試
- 防止暴力破解：登入端點加 rate limit
- 可觀測性：結構化日誌 + 健康檢查端點
- 設定安全：啟動時驗證所有必填環境變數
- 認證強化：短效 access token + 長效 refresh token
- 即時推送：WebSocket 取代 polling

**Non-Goals:**
- Redis 快取層（本次不引入新基礎設施依賴）
- E2E 測試（Playwright/Cypress）
- 前端單元測試
- CDN / 物件儲存
- 將 access token 移至 httpOnly Cookie（本次僅 refresh token 用 Cookie，access token 保留 localStorage）

## Decisions

### 決策 1：測試資料庫策略 — SQLite in-memory

**選擇**：測試時使用 `aiosqlite`（SQLite 非同步驅動）in-memory 資料庫

**理由**：
- 不需要額外的 MariaDB 測試容器，CI 環境零額外設定
- SQLAlchemy 的 ORM 層在 SQLite / MariaDB 上行為一致（標準 SQL）
- pytest fixture 可在每個 test function 後 rollback / drop_all，隔離性強

**替代方案**：test MariaDB（需 docker-compose.test.yml，CI 複雜度高）→ 捨棄

**注意事項**：FFmpeg、yt-dlp 等外部服務呼叫以 mock / patch 處理，不進入資料庫測試範圍

---

### 決策 2：Rate Limiting 儲存 — in-memory（SlowAPI 預設）

**選擇**：`slowapi` + 預設 in-memory 儲存（`InMemoryRateLimiter`）

**理由**：
- 不引入 Redis 等新基礎設施
- 單一 uvicorn 程序下 in-memory 足夠（Docker 單容器部署）
- 未來若改多副本部署，再升級為 Redis 後端（`slowapi` 支援）

**限制設定**：
- `POST /api/auth/login`：5次/分鐘/IP
- `POST /api/videos/upload`：10次/小時/使用者
- `POST /api/videos/download`：10次/小時/使用者

---

### 決策 3：結構化日誌 — 標準 logging + JSON Formatter

**選擇**：使用 Python 標準 `logging` 模組搭配自訂 `JsonFormatter`，透過 FastAPI middleware 注入 `request_id`

**理由**：
- 不引入新依賴（structlog、loguru）
- JSON 格式相容於 Grafana Loki、Datadog、CloudWatch 等主流平台
- `request_id`（UUID4）在 middleware 生成並透過 `contextvars` 傳遞

**替代方案**：`structlog`（功能強但有學習曲線）→ 捨棄，保持依賴精簡

---

### 決策 4：Refresh Token 儲存 — 資料庫表

**選擇**：新增 `refresh_tokens` 資料庫表儲存 Refresh Token

**欄位**：`id, user_id, token_hash（sha256）, expires_at, created_at, revoked`

**理由**：
- 不引入 Redis
- 支援強制登出（revoke）、多裝置管理
- `token_hash` 儲存雜湊值，原始 token 只在回傳時出現一次

**Token 對策略**：
- Access Token：有效期 15 分鐘（`JWT_ACCESS_EXPIRE_MINUTES`，預設 15）
- Refresh Token：有效期 7 天（`JWT_REFRESH_EXPIRE_DAYS`，預設 7），httpOnly Cookie
- 前端 axios interceptor：401 時自動呼叫 `/api/auth/refresh` 換新 access token

---

### 決策 5：WebSocket 連線管理 — in-process ConnectionManager

**選擇**：FastAPI `WebSocket` + 應用層 `ConnectionManager`（dict 管理）

**實作**：
```
video_id → Set[WebSocket]
```
- 下載進度更新時，broadcast 給訂閱該 `video_id` 的所有連線
- 連線斷開自動清理

**理由**：
- 不引入 Redis pub/sub
- 單容器部署下，in-process dict 完全足夠
- 前端保留 polling 作為 WebSocket 不支援時的 fallback

---

### 決策 6：Config Management — pydantic-settings

**選擇**：使用 `pydantic-settings`（`BaseSettings`）建立 `Settings` 類別

**結構**：`backend/config.py`，所有設定集中於此，透過 `@lru_cache` 快取 singleton

**理由**：
- pydantic-settings 與現有 pydantic v2 整合無縫
- 啟動時自動驗證必填項目，缺少時立即報錯
- 型別安全：`DATABASE_URL: str`、`JWT_ACCESS_EXPIRE_MINUTES: int = 15`

---

### 決策 7：CI/CD — GitHub Actions 雙工作流

**工作流設計**：
- `backend-ci.yml`：push / PR → ruff lint + pytest（aiosqlite 測試）
- `frontend-ci.yml`：push / PR → eslint + tsc --noEmit

**觸發條件**：`push` to any branch + `pull_request` to main

**不引入**：自動部署（CD），避免生產環境設定複雜化

---

### 決策 8：移除死依賴 — 直接刪除

`librosa==0.10.2` 與 `scipy==1.14.1` 直接從 `requirements.txt` 移除。
掃描確認後端程式碼中無任何 `import librosa` / `import scipy`。

## Risks / Trade-offs

- **SQLite vs MariaDB 差異**：SQLite 不支援某些 MariaDB 特性（如 FULLTEXT、某些 JSON 函數）→ 測試範圍限於 SQLAlchemy ORM 操作，不測資料庫原生語法
- **In-memory rate limit 重啟歸零**：容器重啟後限制計數清空 → 可接受，本次不引入 Redis
- **Refresh Token 資料庫查詢**：每次 refresh 需查 DB → 加索引（`token_hash` 欄位）緩解
- **WebSocket 多副本問題**：in-process dict 在多副本部署時無法共享狀態 → 本次單容器不受影響，未來擴展時需 Redis pub/sub

## Migration Plan

1. 移除 librosa/scipy 並重建 Docker image
2. 新增 `backend/config.py`，逐步替換各模組的 `os.getenv()`
3. 新增 Alembic migration：`refresh_tokens` 表
4. 實作 refresh token 端點與前端 interceptor
5. 新增 `backend/tests/` 測試目錄與基礎 fixtures
6. 新增 `.github/workflows/`
7. 新增 rate limiting middleware
8. 新增 JSON logging middleware + `/api/health` 端點
9. 新增 WebSocket 端點，前端移除 polling

**Rollback**：各步驟為獨立 PR，任一步驟可獨立回滾

## Open Questions

- Access Token 有效期從 1440 分鐘縮短至 15 分鐘，現有登入使用者的 token 會立即失效 → 部署時需通知或強制重新登入一次
- `/api/health` 是否需要認證保護？→ 建議不需要（監控系統需無認證存取）
