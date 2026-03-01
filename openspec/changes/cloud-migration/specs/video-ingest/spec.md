## MODIFIED Requirements

### Requirement: Presigned PUT 影片上傳（S3-only）

系統 SHALL 提供 Presigned PUT URL 讓前端直接上傳影片至 S3。multipart POST 端點已移除。

#### Scenario: 取得 Presigned PUT 上傳 URL

- **WHEN** 使用者呼叫 `GET /api/videos/upload-url?filename=game.mp4&content_type=video/mp4`
- **THEN** 系統驗證 content_type 在白名單內、sanitize filename，建立 Video 記錄（status=pending），回傳 `{ upload_url, video_id, key }`，upload_url 有效期 900 秒

#### Scenario: 確認上傳並 filetype 二次驗證

- **WHEN** 前端上傳成功後呼叫 `POST /api/videos/{id}/confirm`
- **THEN** 系統從 S3 下載前 262 bytes 進行 filetype 驗證：
  - 驗證通過：背景觸發縮圖生成，Video 狀態更新為 `completed`
  - 驗證失敗：刪除 S3 物件，Video 狀態更新為 `failed`

#### Scenario: 串流影片

- **WHEN** 使用者呼叫 `GET /api/videos/{id}/stream`
- **THEN** 系統回傳 HTTP 302，Location 為 S3 Presigned GET URL（有效期 1800 秒）

### Requirement: YouTube 下載上傳至 S3

yt-dlp 下載完成後 SHALL 自動將影片上傳至 S3 並刪除本地暫存。

#### Scenario: YouTube 下載後上傳

- **WHEN** yt-dlp 成功下載影片至本地暫存
- **THEN** 系統呼叫 `storage_service.upload_file()` 上傳至 S3，上傳成功後刪除暫存，更新 Video 的 `r2_key` 並設狀態為 `completed`

### Requirement: Graceful Shutdown 與 Startup 清理

#### Scenario: SIGTERM 處理

- **WHEN** 應用程式收到 SIGTERM
- **THEN** 將所有狀態為 `downloading` 的 Video 標記為 `failed`，再關閉

#### Scenario: Startup 清理 orphaned pending

- **WHEN** 應用程式啟動
- **THEN** 將超過 1 小時仍為 `pending` 的 Video 標記為 `failed`
