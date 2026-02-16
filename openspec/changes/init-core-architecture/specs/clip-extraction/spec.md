## ADDED Requirements

### Requirement: 依標記擷取片段
系統 SHALL 基於標記的時間範圍，使用 FFmpeg 從原始影片切割出獨立的片段檔案。

#### Scenario: 擷取單一標記的片段
- **WHEN** 使用者觸發對特定標記的片段擷取
- **THEN** 系統使用 FFmpeg 切割該時間範圍的影片，儲存至 clips 目錄，並記錄片段中繼資料

#### Scenario: 批次擷取影片所有標記
- **WHEN** 使用者觸發對一部影片所有標記的批次擷取
- **THEN** 系統依序擷取每個標記對應的片段，記錄每個片段的處理狀態

### Requirement: 無重編碼切割
系統 SHALL 預設使用 FFmpeg 的 stream copy 模式（`-c copy`）進行切割，避免重新編碼以提升速度。

#### Scenario: 快速切割
- **WHEN** 系統擷取一個 8 秒的片段
- **THEN** 使用 `-c copy` 模式完成切割，處理時間 SHALL 在數秒內完成

### Requirement: 片段中繼資料
系統 SHALL 記錄每個片段的中繼資料，包含來源影片、對應標記、檔案路徑、時長、檔案大小。

#### Scenario: 查詢片段列表
- **WHEN** 使用者查詢某部影片的所有片段
- **THEN** 系統回傳片段列表，包含 id、對應標記 id、時長、檔案大小、分類標籤、球員編號

### Requirement: 擷取狀態追蹤
系統 SHALL 追蹤每個擷取任務的狀態（pending → processing → completed/failed）。

#### Scenario: 擷取失敗
- **WHEN** FFmpeg 處理過程發生錯誤
- **THEN** 系統將該片段狀態設為 failed，記錄錯誤訊息

### Requirement: 刪除片段
系統 SHALL 支援刪除片段的檔案與資料庫記錄。

#### Scenario: 刪除片段
- **WHEN** 使用者刪除一個片段
- **THEN** 系統刪除片段檔案與資料庫記錄
