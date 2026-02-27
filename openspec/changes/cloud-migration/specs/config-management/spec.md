## ADDED Requirements

### Requirement: 雲端儲存設定欄位
`Settings` 類別 SHALL 新增 Cloudflare R2 相關設定欄位與 Feature Flag 欄位。當 `STORAGE_BACKEND=r2` 時，R2 相關欄位 MUST 皆有值，否則應用程式啟動時 SHALL 拋出 `ValidationError`。

#### Scenario: R2 後端設定完整
- **WHEN** `STORAGE_BACKEND=r2` 且 R2_ACCESS_KEY_ID、R2_SECRET_ACCESS_KEY、R2_BUCKET_NAME、R2_ENDPOINT_URL 均已設定
- **THEN** 應用程式正常啟動

#### Scenario: R2 後端設定不完整時拒絕啟動
- **WHEN** `STORAGE_BACKEND=r2` 但任一 R2 設定欄位為空字串
- **THEN** 應用程式啟動時 SHALL 拋出 `ValidationError` 並顯示缺少的欄位名稱

#### Scenario: Local 後端不驗證 R2 設定
- **WHEN** `STORAGE_BACKEND=local`（預設值）
- **THEN** R2 相關欄位為空字串時應用程式仍正常啟動

#### Scenario: Feature Flag 讀取
- **WHEN** 任何模組呼叫 `get_settings().enable_clips`
- **THEN** 回傳環境變數 `ENABLE_CLIPS` 的 bool 值，未設定時預設為 `True`
