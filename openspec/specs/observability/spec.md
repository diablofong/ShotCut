## ADDED Requirements

### Requirement: 結構化 JSON 日誌
後端所有 API 請求 MUST 輸出 JSON 格式日誌，包含 request_id、路徑、方法、狀態碼、耗時。

#### Scenario: API 請求日誌記錄
- **WHEN** 任意 HTTP 請求完成
- **THEN** 輸出一筆 JSON 日誌，含以下欄位：
  - `timestamp`（ISO 8601）
  - `level`（INFO / ERROR）
  - `request_id`（UUID4，每次請求唯一）
  - `method`（GET / POST 等）
  - `path`（請求路徑）
  - `status_code`（HTTP 狀態碼）
  - `duration_ms`（處理耗時，毫秒）

#### Scenario: request_id 傳遞
- **WHEN** 請求包含 `X-Request-ID` header
- **THEN** 使用該值作為 request_id；否則自動生成 UUID4

### Requirement: 錯誤日誌包含 request_id
後端 exception 日誌 MUST 包含對應的 request_id，方便追蹤。

#### Scenario: 500 錯誤日誌
- **WHEN** API 處理過程發生未預期 exception
- **THEN** 日誌輸出 ERROR level，含 request_id、exception 類型與 traceback

### Requirement: 健康檢查端點
`GET /api/health` MUST 提供系統健康狀態，包含資料庫連線檢查。

#### Scenario: 系統正常
- **WHEN** GET `/api/health`，資料庫可連線
- **THEN** 回傳 200，body 為：
  ```json
  {
    "status": "healthy",
    "database": "ok",
    "timestamp": "<ISO 8601>"
  }
  ```

#### Scenario: 資料庫連線失敗
- **WHEN** GET `/api/health`，資料庫無法連線
- **THEN** 回傳 503，body 為：
  ```json
  {
    "status": "unhealthy",
    "database": "error",
    "timestamp": "<ISO 8601>"
  }
  ```

#### Scenario: 健康檢查不需要認證
- **WHEN** 未帶任何 token 請求 GET `/api/health`
- **THEN** 正常回傳健康狀態，不回傳 401
