## ADDED Requirements

### Requirement: 儲存後端抽象層（StorageService）
系統 SHALL 透過 `StorageService` 抽象層統一管理影片與縮圖的儲存操作，支援 `local`（本地檔案系統）與 `r2`（Cloudflare R2）兩種後端。儲存後端 MUST 由環境變數 `STORAGE_BACKEND` 決定（預設 `local`）。`StorageService` 實例 MUST 透過工廠函式取得，不得直接實例化具體實作類別。

#### Scenario: 取得 Presigned PUT URL（R2 後端）
- **WHEN** `STORAGE_BACKEND=r2` 且後端呼叫 `generate_presigned_put_url(key, content_type)`
- **THEN** 回傳一個有時效的 S3 Presigned PUT URL，有效期 3600 秒

#### Scenario: 取得 Presigned GET URL（R2 後端）
- **WHEN** `STORAGE_BACKEND=r2` 且後端呼叫 `generate_presigned_get_url(key)`
- **THEN** 回傳一個有時效的 S3 Presigned GET URL，有效期 3600 秒

#### Scenario: 刪除物件（R2 後端）
- **WHEN** `STORAGE_BACKEND=r2` 且後端呼叫 `delete_object(key)`
- **THEN** 從 R2 Bucket 刪除對應物件，回傳 `True`；若物件不存在回傳 `False`

#### Scenario: 上傳本地檔案至 R2
- **WHEN** `STORAGE_BACKEND=r2` 且後端呼叫 `upload_file(local_path, key)`
- **THEN** 將本地檔案上傳至 R2 指定 key，上傳完成後 SHALL 刪除本地暫存檔案，回傳 `True`

#### Scenario: Local 後端不支援 Presigned URL
- **WHEN** `STORAGE_BACKEND=local` 且後端呼叫 `generate_presigned_put_url`
- **THEN** 系統 SHALL 拋出 `NotImplementedError`

#### Scenario: R2 設定不完整時拒絕啟動
- **WHEN** `STORAGE_BACKEND=r2` 但 `R2_ACCESS_KEY_ID`、`R2_SECRET_ACCESS_KEY`、`R2_BUCKET_NAME`、`R2_ENDPOINT_URL` 任一未設定
- **THEN** 應用程式啟動時 SHALL 拋出 `ValidationError` 並中止

### Requirement: Presigned PUT 影片上傳流程
系統 SHALL 提供 Presigned PUT URL，讓前端直接上傳影片至 R2，不經過應用程式伺服器。

#### Scenario: 取得上傳 URL
- **WHEN** `STORAGE_BACKEND=r2` 且使用者呼叫 `GET /api/videos/upload-url?filename=game.mp4&content_type=video/mp4`
- **THEN** 系統建立 Video 記錄（status=pending），回傳 `{ upload_url, video_id, key }`

#### Scenario: 前端確認上傳完成
- **WHEN** 前端上傳至 R2 成功後呼叫 `POST /api/videos/{id}/confirm`
- **THEN** 系統觸發縮圖生成並將 Video 狀態更新為 `completed`

#### Scenario: 影片串流（R2 後端）
- **WHEN** `STORAGE_BACKEND=r2` 且使用者呼叫 `GET /api/videos/{id}/stream`
- **THEN** 系統回傳 HTTP 302，Location 為 R2 Presigned GET URL，有效期 3600 秒

#### Scenario: 影片串流（Local 後端）
- **WHEN** `STORAGE_BACKEND=local` 且使用者呼叫 `GET /api/videos/{id}/stream`
- **THEN** 系統回傳原有的 Range-based streaming 回應，行為不變

### Requirement: 刪除影片同步清除 R2 物件
系統刪除 Video 記錄時 SHALL 同步從對應儲存後端刪除影片檔案與縮圖。

#### Scenario: 刪除影片（R2 後端）
- **WHEN** `STORAGE_BACKEND=r2` 且使用者刪除影片
- **THEN** 系統從 R2 刪除 `video.r2_key` 對應的物件及縮圖，再刪除資料庫記錄
