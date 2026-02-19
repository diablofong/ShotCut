## ADDED Requirements

### Requirement: WebSocket 下載進度端點
後端 MUST 提供 `WS /api/videos/{video_id}/ws/progress` 端點，推送影片下載進度。

#### Scenario: 連線至進度 WebSocket
- **WHEN** 前端 WebSocket 連線至 `/api/videos/{video_id}/ws/progress`（帶 `?token=<access_token>`）
- **THEN** 伺服器接受連線，開始推送進度訊息

#### Scenario: 推送進度訊息格式
- **WHEN** 影片下載進度更新
- **THEN** 伺服器向所有訂閱該 video_id 的 WebSocket 連線推送 JSON 訊息：
  ```json
  {
    "status": "downloading",
    "progress": 45.2,
    "speed": "2.5 MiB/s",
    "eta": 32
  }
  ```

#### Scenario: 下載完成推送
- **WHEN** 影片下載完成
- **THEN** 推送 `{"status": "completed", "progress": 100}` 後伺服器主動關閉連線

#### Scenario: 下載失敗推送
- **WHEN** 影片下載失敗
- **THEN** 推送 `{"status": "failed", "error": "<錯誤訊息>"}` 後伺服器主動關閉連線

### Requirement: 連線管理
後端 MUST 管理所有 WebSocket 連線，連線斷開時自動清理。

#### Scenario: 客戶端斷線自動清理
- **WHEN** 客戶端 WebSocket 連線意外中斷
- **THEN** 伺服器從 ConnectionManager 移除該連線，不造成記憶體洩漏

#### Scenario: 同一影片多個連線
- **WHEN** 同一 video_id 有多個 WebSocket 連線（如不同瀏覽器分頁）
- **THEN** 進度更新廣播至所有連線

### Requirement: 前端移除 Polling
前端 `VideoDetailPage` MUST 移除每秒 setInterval polling `/api/videos/{id}/status`，改用 WebSocket 接收進度。

#### Scenario: 前端 WebSocket 連線
- **WHEN** 使用者開啟有下載中影片的頁面
- **THEN** 前端自動建立 WebSocket 連線，接收進度更新並更新 UI，不發送 HTTP polling 請求

#### Scenario: WebSocket 連線失敗降級
- **WHEN** WebSocket 連線無法建立（網路限制）
- **THEN** 前端降級至每 3 秒 polling `/api/videos/{id}/status` 作為備援
