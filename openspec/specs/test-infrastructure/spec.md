## ADDED Requirements

### Requirement: 後端測試環境設定
後端測試 SHALL 使用 pytest + pytest-asyncio + httpx，以 SQLite in-memory 作為測試資料庫，不依賴外部 MariaDB 服務。

#### Scenario: 執行後端測試
- **WHEN** 執行 `pytest backend/tests/`
- **THEN** 所有測試使用獨立的 SQLite in-memory 資料庫完成，不影響開發或生產資料庫

#### Scenario: 測試隔離
- **WHEN** 每個測試函式執行完畢
- **THEN** 資料庫狀態完全重置，各測試間互不干擾

### Requirement: 測試 Fixture 基礎架構
測試 MUST 提供共用 fixtures：async test client、資料庫 session、測試使用者（一般用戶 / 管理員）。

#### Scenario: 取得認證 test client
- **WHEN** 測試需要已登入使用者的 HTTP client
- **THEN** fixture 自動建立測試使用者、取得 JWT token，並回傳帶有 Authorization header 的 `AsyncClient`

### Requirement: 認證 API 整合測試
`/api/auth/login` 端點 MUST 有整合測試涵蓋登入成功與失敗情境。

#### Scenario: 登入成功
- **WHEN** POST `/api/auth/login` 帶有正確帳號密碼
- **THEN** 回傳 200 及含 `access_token` 的 JSON

#### Scenario: 登入失敗
- **WHEN** POST `/api/auth/login` 帶有錯誤密碼
- **THEN** 回傳 401

### Requirement: 影片 API 整合測試
影片相關端點（列表、詳情、刪除）MUST 有整合測試。

#### Scenario: 取得影片列表
- **WHEN** 已認證使用者 GET `/api/videos`
- **THEN** 回傳 200 及影片陣列

#### Scenario: 未認證存取
- **WHEN** 未帶 token 存取 `/api/videos`
- **THEN** 回傳 401

### Requirement: 標記 API 整合測試
標記相關端點（建立、列表、刪除）MUST 有整合測試。

#### Scenario: 建立標記
- **WHEN** 已認證使用者 POST `/api/videos/{video_id}/marks` 帶有有效 payload
- **THEN** 回傳 200 及建立的標記資料

#### Scenario: 其他使用者無法刪除標記
- **WHEN** 非擁有者使用者 DELETE `/api/marks/{mark_id}`
- **THEN** 回傳 403

### Requirement: 分享連結 API 整合測試
分享連結端點（建立、存取、刪除）MUST 有整合測試。

#### Scenario: 公開存取分享連結
- **WHEN** 未認證請求 GET `/api/shares/{token}`（有效 token）
- **THEN** 回傳 200 及精華剪輯資訊，不需要 Authorization header

#### Scenario: 存取過期分享連結
- **WHEN** GET `/api/shares/{token}`（已過期 token）
- **THEN** 回傳 410
