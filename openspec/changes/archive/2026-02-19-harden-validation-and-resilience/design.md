## Context

ShotCut 已完成第一輪安全修復（環境變數、CORS、IDOR、Range 驗證等），但仍存在輸入驗證不足、FFmpeg 無 timeout、前端錯誤處理缺失、列表無分頁等問題。本次修復以強化驗證與韌性為主軸。

## Goals / Non-Goals

**Goals:**
- 所有 Pydantic request model 加入嚴格驗證
- FFmpeg subprocess 加入 timeout 與錯誤訊息遮蔽
- 前端顯示實際錯誤、加入 Error Boundary
- 列表端點支援分頁
- 加入 /health 健康檢查端點
- 下載/串流端點二次驗證 file_path 在合法目錄內
- 統一 API 回應格式

**Non-Goals:**
- Rate limiting（需引入新依賴，另案處理）
- CSRF 防護（Bearer token 架構下優先級較低）
- Docker 非 root 執行（需調整 volume 權限，另案處理）
- 自動化測試（規模較大，另案處理）

## Decisions

### D1: Pydantic Field 驗證策略
使用 Pydantic `Field()` 與 `model_validator` 在 request model 層面驗證：
- 時間值 >= 0
- `start_time < end_time`（建立標記時）
- `category` 使用 `Literal` 限制白名單
- `player_numbers` 元素範圍 0-999
- `label` 長度上限 200 字
- `start_offset`、`end_offset` 範圍 0-60 秒

**理由**: 在最外層攔截，避免無效資料進入 service 層。

### D2: FFmpeg Timeout
所有 `subprocess.run()` 加入 `timeout=300`（5 分鐘），捕捉 `subprocess.TimeoutExpired`。

**理由**: 防止惡意或超長影片造成 FFmpeg 無限掛起。

### D3: FFmpeg 錯誤訊息遮蔽
`clip_service` 與 `highlight_service` 中 FFmpeg 失敗的 `error_message` 改為通用訊息「影片處理失敗」，完整 stderr 僅寫入 log。

**理由**: 避免 FFmpeg stderr 洩漏系統路徑等敏感資訊。

### D4: 列表分頁
列表端點（marks、clips、highlights、videos）加入 `limit`（預設 100、上限 500）與 `offset`（預設 0）查詢參數。保持向下相容：不帶參數時回傳前 100 筆。

**理由**: 防止大量資料一次載入造成記憶體與效能問題。

### D5: file_path 二次驗證
在 download/stream 端點回傳檔案前，用 `os.path.realpath()` 驗證路徑在 `UPLOAD_DIR`、`CLIP_DIR` 或 `HIGHLIGHT_DIR` 內。

**理由**: 即使 DB 中 file_path 被篡改，也不會讀取到系統任意檔案。

### D6: 前端 Error Boundary + 錯誤顯示
- 新增 `ErrorBoundary` 元件包裹主要路由
- 各頁面的 catch 區塊改為顯示 error state
- 區分「載入中」、「無資料」、「載入失敗」三種狀態

**理由**: 提升使用體驗，讓使用者能判斷狀態並採取行動。

### D7: 統一 API 錯誤回應格式
刪除端點統一回傳 `{"detail": "已刪除"}`，取代 `{"ok": true}`。

**理由**: 與 FastAPI 預設的 HTTPException 格式一致。

### D8: 健康檢查端點
在 `backend/main.py` 加入 `GET /health`，回傳 `{"status": "ok"}`，不需認證。

**理由**: 供 Docker HEALTHCHECK 與監控系統使用。

## Risks / Trade-offs

- [分頁預設 100] → 現有前端不帶分頁參數時只取前 100 筆，大量資料需前端實作分頁 UI（本次暫不處理前端分頁 UI，僅後端支援）
- [FFmpeg timeout 5 分鐘] → 超長影片（數小時比賽）可能 timeout → 可透過環境變數 FFMPEG_TIMEOUT 覆蓋
- [Pydantic 嚴格驗證] → 可能拒絕舊版前端發送的寬鬆資料 → 驗證值範圍設定足夠寬鬆以相容
