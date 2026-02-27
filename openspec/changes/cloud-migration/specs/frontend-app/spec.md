## ADDED Requirements

### Requirement: R2 後端的 Presigned PUT 上傳流程
當環境變數 `VITE_STORAGE_BACKEND=r2` 時，前端上傳影片 SHALL 改用 Presigned PUT 流程，直接將檔案傳輸至 Cloudflare R2，不經過後端伺服器。原有 multipart POST 流程（`VITE_STORAGE_BACKEND` 未設定或非 `r2`）MUST 保持不變。

#### Scenario: R2 模式上傳影片
- **WHEN** `VITE_STORAGE_BACKEND=r2` 且使用者選擇影片檔案並觸發上傳
- **THEN** 前端 SHALL 依序執行：
  1. `GET /api/videos/upload-url` 取得 `{ upload_url, video_id, key }`
  2. 使用 XHR PUT 將檔案直接傳至 `upload_url`（R2 Presigned URL），並更新上傳進度
  3. `POST /api/videos/{video_id}/confirm` 通知後端處理完成
  4. 顯示上傳成功，刷新影片列表

#### Scenario: 本地模式維持原有流程
- **WHEN** `VITE_STORAGE_BACKEND` 未設定或值非 `r2`，且使用者選擇影片檔案並觸發上傳
- **THEN** 前端 SHALL 使用 multipart POST 將檔案傳至 `/api/videos/upload`，行為與現有完全相同

#### Scenario: R2 上傳進度回報
- **WHEN** 前端正在執行 R2 Presigned PUT 上傳
- **THEN** 前端 SHALL 透過 XHR progress 事件更新上傳進度百分比，讓使用者可見傳輸狀態
