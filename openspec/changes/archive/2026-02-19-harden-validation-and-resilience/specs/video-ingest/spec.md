## MODIFIED Requirements

### Requirement: 影片列表與詳情
系統 SHALL 提供影片列表查詢與單一影片詳情查詢功能。列表查詢 SHALL 支援 `limit`（預設 100、上限 500）與 `offset`（預設 0）分頁參數。

#### Scenario: 查詢影片列表
- **WHEN** 使用者請求影片列表
- **THEN** 系統回傳影片記錄，包含 id、標題、來源類型、狀態、時長、建立時間

#### Scenario: 分頁查詢影片列表
- **WHEN** 使用者請求影片列表並帶入 `limit=20&offset=0`
- **THEN** 系統回傳前 20 筆影片

#### Scenario: 查詢影片詳情
- **WHEN** 使用者請求特定影片的詳情
- **THEN** 系統回傳該影片的完整資訊，包含所有標記數量與片段數量

### Requirement: 下載片段
下載與串流端點 MUST 驗證 file_path 在合法的 uploads 目錄內，防止任意檔案讀取。

#### Scenario: 串流影片
- **WHEN** 使用者請求串流影片
- **THEN** 系統驗證 file_path 在 UPLOAD_DIR 內後回傳影片串流

#### Scenario: file_path 指向非法目錄
- **WHEN** 影片的 file_path 指向 UPLOAD_DIR 以外的路徑
- **THEN** 系統 SHALL 回傳 404 錯誤
