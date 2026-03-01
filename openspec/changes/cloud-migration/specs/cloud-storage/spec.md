## MODIFIED Requirements

### Requirement: S3StorageService（唯一儲存後端）

系統 SHALL 透過 `S3StorageService` 統一管理影片與縮圖的儲存操作，相容於任何 S3-compatible 服務（MinIO、Cloudflare R2、AWS S3、Backblaze B2）。`LocalStorageService` 已移除。工廠函式 `get_storage_service()` 直接回傳 `S3StorageService` 實例。

#### Scenario: 取得 Presigned PUT URL

- **WHEN** 後端呼叫 `generate_presigned_put_url(key, content_type)`
- **THEN** 回傳有效期 **900 秒**的 S3 Presigned PUT URL

#### Scenario: 取得 Presigned GET URL

- **WHEN** 後端呼叫 `generate_presigned_get_url(key)`
- **THEN** 回傳有效期 **1800 秒**的 S3 Presigned GET URL

#### Scenario: 刪除物件

- **WHEN** 後端呼叫 `delete_object(key)`
- **THEN** 從 bucket 刪除對應物件，回傳 `True`；若物件不存在回傳 `False`

#### Scenario: 上傳本地檔案

- **WHEN** 後端呼叫 `upload_file(local_path, key)`
- **THEN** 將本地檔案上傳至 S3，上傳完成後 SHALL 刪除本地暫存，回傳 `True`

#### Scenario: S3 設定不完整時拒絕啟動

- **WHEN** `S3_ACCESS_KEY_ID`、`S3_SECRET_ACCESS_KEY`、`S3_BUCKET_NAME`、`S3_ENDPOINT_URL` 任一未設定
- **THEN** 應用程式啟動時 SHALL 拋出 `ValidationError` 並中止

### Requirement: Presigned PUT 影片上傳流程

系統 SHALL 提供 Presigned PUT URL，讓前端直接上傳影片至 S3，不經過應用程式伺服器。

#### Scenario: 取得上傳 URL

- **WHEN** 使用者呼叫 `GET /api/videos/upload-url?filename=game.mp4&content_type=video/mp4`
- **THEN** 系統建立 Video 記錄（status=pending），回傳 `{ upload_url, video_id, key }`

#### Scenario: 確認上傳完成

- **WHEN** 前端上傳至 S3 成功後呼叫 `POST /api/videos/{id}/confirm`
- **THEN** 系統觸發 filetype 二次驗證、縮圖生成，並將 Video 狀態更新為 `completed`；驗證失敗則刪除 S3 物件並標記 `failed`

#### Scenario: 影片串流

- **WHEN** 使用者呼叫 `GET /api/videos/{id}/stream`
- **THEN** 系統回傳 HTTP 302，Location 為 S3 Presigned GET URL（有效期 1800 秒）

### Requirement: 刪除影片同步清除 S3 物件

#### Scenario: 刪除影片

- **WHEN** 使用者刪除影片
- **THEN** 系統從 S3 刪除 `video.r2_key` 對應的物件及縮圖，再刪除資料庫記錄
