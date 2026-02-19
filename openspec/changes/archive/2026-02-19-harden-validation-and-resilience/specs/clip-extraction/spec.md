## MODIFIED Requirements

### Requirement: 依標記擷取片段
系統 SHALL 基於標記的時間範圍，使用 FFmpeg 從原始影片切割出獨立的片段檔案。FFmpeg subprocess MUST 設定 timeout（預設 300 秒），超時 SHALL 將片段狀態設為 failed。

#### Scenario: 擷取單一標記的片段
- **WHEN** 使用者觸發對特定標記的片段擷取
- **THEN** 系統使用 FFmpeg 切割該時間範圍的影片，儲存至 clips 目錄，並記錄片段中繼資料

#### Scenario: 批次擷取影片所有標記
- **WHEN** 使用者觸發對一部影片所有標記的批次擷取
- **THEN** 系統依序擷取每個標記對應的片段，記錄每個片段的處理狀態

#### Scenario: FFmpeg 處理超時
- **WHEN** FFmpeg 切割單一片段超過 300 秒
- **THEN** 系統 SHALL 終止 FFmpeg process，將片段狀態設為 failed，記錄 timeout 錯誤

### Requirement: 擷取狀態追蹤
系統 SHALL 追蹤每個擷取任務的狀態（pending → processing → completed/failed）。FFmpeg 失敗時的 error_message MUST 為通用訊息，不得包含 FFmpeg stderr 原始輸出。

#### Scenario: 擷取失敗
- **WHEN** FFmpeg 處理過程發生錯誤
- **THEN** 系統將該片段狀態設為 failed，error_message 記錄為「影片處理失敗」，完整 stderr 僅寫入伺服器 log

### Requirement: 片段篩選
系統 SHALL 支援按分類（category）與球員編號（player_number）篩選片段列表。列表查詢 SHALL 支援 `limit`（預設 100、上限 500）與 `offset`（預設 0）分頁參數。

#### Scenario: 按分類篩選片段
- **WHEN** 使用者在片段管理頁面選擇「進攻」分類
- **THEN** 系統回傳所有分類為 offense 的片段

#### Scenario: 按球員篩選片段
- **WHEN** 使用者在片段管理頁面選擇球員 7
- **THEN** 系統回傳所有關聯球員 7 的片段

#### Scenario: 分頁查詢
- **WHEN** 使用者查詢片段列表並帶入 `limit=20&offset=0`
- **THEN** 系統回傳前 20 筆片段

### Requirement: 下載片段
系統 SHALL 提供片段檔案下載端點。下載前 MUST 驗證 file_path 在合法的 clips 目錄內。

#### Scenario: 下載片段
- **WHEN** 使用者請求下載已完成的片段
- **THEN** 系統驗證 file_path 在 CLIP_DIR 內後回傳檔案

#### Scenario: file_path 指向非法目錄
- **WHEN** 片段的 file_path 指向 CLIP_DIR 以外的路徑
- **THEN** 系統 SHALL 回傳 404 錯誤
