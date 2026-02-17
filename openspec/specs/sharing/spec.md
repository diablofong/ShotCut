## ADDED Requirements

### Requirement: 建立分享連結
系統 SHALL 支援為精華剪輯產生具有唯一識別碼的分享連結。

#### Scenario: 建立分享連結
- **WHEN** 使用者對一部精華剪輯建立分享連結
- **THEN** 系統產生唯一 token，回傳完整的分享 URL

#### Scenario: 為不存在的精華剪輯建立連結
- **WHEN** 使用者對不存在的精華剪輯 ID 建立分享連結
- **THEN** 系統 SHALL 回傳 404 錯誤

### Requirement: 透過分享連結存取
系統 SHALL 允許任何人透過分享連結觀看精華剪輯，無需登入。

#### Scenario: 有效分享連結存取
- **WHEN** 訪客透過有效的分享連結存取
- **THEN** 系統提供精華剪輯的播放頁面，可直接觀看影片

#### Scenario: 無效分享連結存取
- **WHEN** 訪客透過無效或不存在的 token 存取
- **THEN** 系統 SHALL 回傳 404 頁面

### Requirement: 分享連結管理
系統 SHALL 提供分享連結的查詢與刪除功能。

#### Scenario: 查詢分享連結列表
- **WHEN** 使用者查詢某部精華剪輯的分享連結
- **THEN** 系統回傳該精華剪輯的所有分享連結，包含 token、建立時間、存取次數

#### Scenario: 刪除分享連結
- **WHEN** 使用者刪除一個分享連結
- **THEN** 系統使該 token 失效，後續存取 SHALL 回傳 404

### Requirement: 存取計數
系統 SHALL 記錄每個分享連結的存取次數。

#### Scenario: 記錄存取
- **WHEN** 訪客透過分享連結觀看精華剪輯
- **THEN** 系統將該連結的存取次數加 1
