## Context

ShotCut 是一個籃球比賽影片標記與片段擷取工具，即將公開發佈。經安全審查發現多項安全漏洞與程式碼品質問題。目前的架構為 FastAPI + React SPA，透過 Docker Compose 部署，所有認證使用 JWT。

現有問題分為三個層級：
1. **緊急安全漏洞**：路徑遍歷、IDOR、硬編碼 Secret
2. **高危問題**：CORS 全開、無檔案上限、Range 未驗證
3. **品質問題**：時區不一致、資源洩漏、前端 polling bug

## Goals / Non-Goals

**Goals:**
- 修復所有已知安全漏洞，達到可公開發佈的安全水準
- 移除所有硬編碼的密碼與密鑰 fallback
- 確保所有端點的權限驗證一致
- 修復已知的程式碼品質問題

**Non-Goals:**
- 不實作 rate limiting（需要額外的基礎設施如 Redis，留待後續）
- 不將 JWT 從 localStorage 遷移至 httpOnly cookie（需要大規模重構認證流程）
- 不新增 JWT token 撤銷/黑名單機制
- 不變更 Docker 容器為非 root 用戶（需調整檔案權限策略）
- 不修改前端 token 透過 URL query 傳遞的方式（需要改用 service worker 或其他機制）

## Decisions

### D1: 環境變數無 fallback，啟動時驗證

移除所有 `os.getenv("KEY", "default_value")` 中的 fallback 預設值。改為啟動時若缺少必要環境變數直接拋出錯誤。

**替代方案**：保留 fallback 但加入啟動警告 → 不採用，因為開發者容易忽略警告，直接報錯更安全。

**影響檔案**：`security.py`、`database.py`、`videos.py`、`seed_admin.py`、`alembic/env.py`

### D2: SPA fallback 使用 `os.path.realpath` 驗證

在 `spa_fallback` 中，用 `os.path.realpath(file_path)` 正規化路徑後檢查是否仍在 `frontend_dist` 目錄下。不在則直接返回 `index.html`。

**替代方案**：使用 allowlist 機制 → 不採用，過於繁瑣且需要隨前端更新。

### D3: 精華剪輯端點加入 verify_highlight_owner 輔助函式

在 `auth/dependencies.py` 新增 `verify_highlight_owner()` 函式，模式與現有 `verify_video_owner()` 一致。套用至 stream、download、thumbnail 三個端點。

**替代方案**：在每個端點內部各自檢查 → 不採用，會有程式碼重複且容易遺漏。

### D4: 檔案上傳以串流方式讀取並限制大小

不使用 `await file.read()`（會一次載入全部至記憶體），改為以 chunk 方式寫入磁碟並即時檢查累積大小。透過環境變數 `MAX_UPLOAD_SIZE_MB` 控制上限（預設 2048MB）。

### D5: CORS origin 從環境變數讀取

新增環境變數 `CORS_ORIGINS`，以逗號分隔的 origin 清單。開發環境可設為 `http://localhost:5173,http://localhost:8000`，生產環境設為實際域名。

### D6: Range header 統一驗證函式

建立共用的 `_parse_range_header(range_header, file_size)` 函式，處理所有邊界情況（負數、超出範圍、無效格式），於 4 個串流端點共用。無效 Range 回傳 416 Range Not Satisfiable。

### D7: 背景下載 engine 用 try-finally 包裹

在 `_async_download()` 中用 `try-finally` 確保 `engine.dispose()` 執行，避免資料庫連線洩漏。

## Risks / Trade-offs

- **[BREAKING] 環境變數必須設定**：移除 fallback 後，所有部署環境（包括開發環境）必須完整設定 `.env`。→ 透過更新 `.env.example` 和 `docker-compose.yml` 的預設值來緩解。
- **[BREAKING] 精華剪輯權限收緊**：原本跨使用者可存取的精華剪輯將被 403 擋下。→ 分享連結不受影響，確保教練/家長仍可透過分享觀看。
- **CORS 可能影響開發環境**：如果忘記設定 `CORS_ORIGINS`，開發時前端無法連線後端。→ `docker-compose.dev.yml` 中預設包含 `localhost` origin。
