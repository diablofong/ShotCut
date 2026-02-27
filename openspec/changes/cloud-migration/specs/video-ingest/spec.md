## ADDED Requirements

### Requirement: R2 後端影片上傳（Presigned PUT）
當 `STORAGE_BACKEND=r2` 時，系統 SHALL 提供 Presigned PUT URL 讓前端直接上傳影片至 R2，原有的 multipart POST 端點 SHALL 在 R2 模式下繼續可用以保持向後相容。

#### Scenario: 取得 Presigned PUT 上傳 URL
- **WHEN** `STORAGE_BACKEND=r2` 且使用者呼叫 `GET /api/videos/upload-url?filename=game.mp4&content_type=video/mp4`
- **THEN** 系統建立 Video 記錄（status=pending，r2_key 已設定），回傳 `{ upload_url, video_id, key }`，upload_url 為有效期 3600 秒的 S3 Presigned PUT URL

#### Scenario: 確認上傳完成並產生縮圖
- **WHEN** 前端上傳影片至 R2 成功後呼叫 `POST /api/videos/{id}/confirm`
- **THEN** 系統在背景觸發縮圖生成（從 R2 暫存下載→FFmpeg 截圖→上傳縮圖至 R2→刪除暫存），並將 Video 狀態更新為 `completed`

#### Scenario: 串流影片（R2 後端）
- **WHEN** `STORAGE_BACKEND=r2` 且使用者呼叫 `GET /api/videos/{id}/stream`
- **THEN** 系統回傳 HTTP 302，Location 為 R2 Presigned GET URL，有效期 3600 秒，瀏覽器直接從 R2 串流

### Requirement: YouTube 下載相容 R2 後端
yt-dlp 下載完成後，當 `STORAGE_BACKEND=r2` 時 SHALL 自動將影片上傳至 R2 並刪除本地暫存。

#### Scenario: YouTube 下載後上傳至 R2
- **WHEN** `STORAGE_BACKEND=r2` 且 yt-dlp 成功下載影片至本地暫存
- **THEN** 系統呼叫 `storage_service.upload_file()` 將影片上傳至 R2，上傳成功後刪除本地暫存，更新 Video 的 `r2_key` 並設狀態為 `completed`
