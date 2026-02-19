## ADDED Requirements

### Requirement: 健康檢查端點
系統 SHALL 提供 `GET /health` 端點，不需認證即可存取，回傳 `{"status": "ok"}`。

#### Scenario: 健康檢查成功
- **WHEN** Docker 或監控系統請求 `GET /health`
- **THEN** 系統回傳 200 OK 與 `{"status": "ok"}`，不需 JWT token
