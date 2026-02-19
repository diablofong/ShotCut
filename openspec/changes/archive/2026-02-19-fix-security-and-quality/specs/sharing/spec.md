## MODIFIED Requirements

### Requirement: 建立分享連結
系統 SHALL 支援為精華剪輯產生具有唯一識別碼的分享連結。分享連結過期判斷 MUST 使用 timezone-aware 的 UTC 時間（`datetime.now(timezone.utc)`），不得使用已棄用的 `datetime.utcnow()`。

#### Scenario: 建立分享連結
- **WHEN** 使用者對一部精華剪輯建立分享連結
- **THEN** 系統產生唯一 token，回傳完整的分享 URL

#### Scenario: 為不存在的精華剪輯建立連結
- **WHEN** 使用者對不存在的精華剪輯 ID 建立分享連結
- **THEN** 系統 SHALL 回傳 404 錯誤

### Requirement: 透過分享連結存取
系統 SHALL 允許任何人透過分享連結觀看精華剪輯，無需登入。串流端點 MUST 驗證 Range header 的合法性（start >= 0、start <= end、end < file_size），無效的 Range SHALL 回傳 416 Range Not Satisfiable。

#### Scenario: 有效分享連結存取
- **WHEN** 訪客透過有效的分享連結存取
- **THEN** 系統提供精華剪輯的播放頁面，可直接觀看影片

#### Scenario: 無效分享連結存取
- **WHEN** 訪客透過無效或不存在的 token 存取
- **THEN** 系統 SHALL 回傳 404 頁面

#### Scenario: 已過期的分享連結存取
- **WHEN** 訪客透過已過期的分享 token 存取
- **THEN** 系統 SHALL 回傳 410 Gone

#### Scenario: 無效的 Range header
- **WHEN** 串流請求包含無效的 Range header（如負數、start > end、超出檔案大小）
- **THEN** 系統 SHALL 回傳 416 Range Not Satisfiable
