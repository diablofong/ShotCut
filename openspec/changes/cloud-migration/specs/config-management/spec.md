## MODIFIED Requirements

### Requirement: S3 設定欄位（統一 S3_* 命名）

`Settings` 類別 SHALL 使用 `S3_*` 前綴的欄位管理物件儲存設定。`STORAGE_BACKEND` 欄位已移除。`R2_*` 舊環境變數透過 model_validator 自動映射到 `S3_*`（向後相容）。啟動時若任一 `S3_*` 欄位為空字串，SHALL 拋出 `ValidationError`。

#### Scenario: S3 設定完整時正常啟動

- **WHEN** `S3_ACCESS_KEY_ID`、`S3_SECRET_ACCESS_KEY`、`S3_BUCKET_NAME`、`S3_ENDPOINT_URL` 均已設定
- **THEN** 應用程式正常啟動

#### Scenario: S3 設定不完整時拒絕啟動

- **WHEN** 任一 S3_* 欄位為空字串
- **THEN** 應用程式啟動時 SHALL 拋出 `ValidationError` 並顯示缺少的欄位名稱

#### Scenario: 舊 R2_* 環境變數向後相容

- **WHEN** 環境中設定了 `R2_ACCESS_KEY_ID`（舊格式）而非 `S3_ACCESS_KEY_ID`
- **THEN** validator 自動映射，應用程式正常啟動

#### Scenario: Feature Flag 讀取

- **WHEN** 任何模組呼叫 `get_settings().enable_clips`
- **THEN** 回傳環境變數 `ENABLE_CLIPS` 的 bool 值，未設定時預設為 `True`

### Requirement: Runtime Config 端點

系統 SHALL 提供 `GET /api/config` 端點供前端 runtime 讀取功能設定。

#### Scenario: 取得功能設定

- **WHEN** 前端呼叫 `GET /api/config`
- **THEN** 回傳 `{ features: { clips: bool, highlights: bool, sharing: bool } }`，不包含任何 S3 credentials 或內部設定
