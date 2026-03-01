## MODIFIED Requirements

### Requirement: Runtime Config 取代 Build-time 環境變數

前端 SHALL 透過 `GET /api/config` runtime 讀取功能設定，移除 `VITE_STORAGE_BACKEND` build-time 環境變數。所有部署使用同一個 Docker image，不需重新 build。

#### Scenario: 初始化時讀取 config

- **WHEN** 前端 app 載入
- **THEN** `useAppConfig` hook 呼叫 `GET /api/config`，取得 `{ features }` 並快取於 React context

### Requirement: Presigned PUT 為唯一上傳路徑

前端上傳影片 SHALL 統一使用 Presigned PUT 流程，移除 multipart POST 分支。

#### Scenario: 上傳影片

- **WHEN** 使用者選擇影片檔案並觸發上傳
- **THEN** 前端依序執行：
  1. `GET /api/videos/upload-url` 取得 `{ upload_url, video_id, key }`
  2. XHR PUT 直接傳至 `upload_url`，更新上傳進度
  3. `POST /api/videos/{video_id}/confirm` 通知後端
  4. 顯示成功，刷新影片列表

#### Scenario: 上傳進度顯示

- **WHEN** 前端正在執行 Presigned PUT 上傳
- **THEN** 透過 XHR progress 事件更新進度百分比，使用者可見傳輸狀態
