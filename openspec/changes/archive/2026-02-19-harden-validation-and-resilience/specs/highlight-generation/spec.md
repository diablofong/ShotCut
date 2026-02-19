## MODIFIED Requirements

### Requirement: FFmpeg 片段合併
系統 SHALL 使用 FFmpeg concat demuxer 合併片段，確保輸出影片播放流暢。FFmpeg subprocess MUST 設定 timeout（預設 300 秒），超時 SHALL 將精華剪輯狀態設為 failed。

#### Scenario: 合併多個片段
- **WHEN** 系統合併 5 個片段為精華剪輯
- **THEN** 使用 FFmpeg concat demuxer 產出連續播放的 mp4 檔案

#### Scenario: FFmpeg 合併超時
- **WHEN** FFmpeg 合併過程超過 300 秒
- **THEN** 系統 SHALL 終止 FFmpeg process，將精華剪輯狀態設為 failed

### Requirement: 產出狀態追蹤
系統 SHALL 追蹤精華剪輯產出任務的狀態（pending → processing → completed/failed）。FFmpeg 失敗時的 error_message MUST 為通用訊息，不得包含 FFmpeg stderr 原始輸出。

#### Scenario: 產出完成
- **WHEN** FFmpeg 合併完成
- **THEN** 系統將狀態更新為 completed，記錄輸出檔案路徑與檔案大小

#### Scenario: 產出失敗
- **WHEN** FFmpeg 合併過程發生錯誤
- **THEN** 系統將狀態設為 failed，error_message 記錄為「影片處理失敗」，完整錯誤僅寫入伺服器 log

### Requirement: 精華剪輯中繼資料
系統 SHALL 記錄每部精華剪輯的中繼資料，包含篩選條件、包含的片段列表、總時長、檔案大小。列表查詢 SHALL 支援 `limit`（預設 100、上限 500）與 `offset`（預設 0）分頁參數。

#### Scenario: 查詢精華剪輯列表
- **WHEN** 使用者查詢精華剪輯列表
- **THEN** 系統回傳精華剪輯，包含 id、篩選條件、片段數量、總時長、建立時間

#### Scenario: 分頁查詢
- **WHEN** 使用者查詢精華剪輯列表並帶入 `limit=20&offset=0`
- **THEN** 系統回傳前 20 筆精華剪輯

### Requirement: 下載精華剪輯
系統 SHALL 提供精華剪輯檔案下載端點。下載端點 MUST 驗證請求者為精華剪輯的擁有者或管理員，非擁有者 SHALL 回傳 403 Forbidden。下載前 MUST 驗證 file_path 在合法的 highlights 目錄內。

#### Scenario: 擁有者下載精華剪輯
- **WHEN** 精華剪輯擁有者請求下載已完成的精華剪輯
- **THEN** 系統驗證 file_path 在 HIGHLIGHT_DIR 內後回傳檔案

#### Scenario: 非擁有者嘗試下載精華剪輯
- **WHEN** 非擁有者且非管理員嘗試下載精華剪輯
- **THEN** 系統 SHALL 回傳 403 Forbidden

#### Scenario: 管理員下載任意精華剪輯
- **WHEN** 管理員請求下載任何精華剪輯
- **THEN** 系統允許下載
