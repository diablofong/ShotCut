## ADDED Requirements

### Requirement: 依球員產出精華剪輯
系統 SHALL 支援篩選特定球員的所有片段，自動合併為一部連續的精華剪輯影片。

#### Scenario: 產出球員 7 的精華剪輯
- **WHEN** 使用者選擇球員編號 7，觸發精華剪輯產出
- **THEN** 系統篩選所有標記球員 7 的片段，依時間順序合併為一部影片，儲存至 highlights 目錄

#### Scenario: 球員無任何片段
- **WHEN** 使用者選擇的球員沒有任何關聯的片段
- **THEN** 系統 SHALL 回傳錯誤訊息，提示該球員無可用片段

### Requirement: 依標籤產出精華剪輯
系統 SHALL 支援篩選特定分類標籤的所有片段，自動合併為精華剪輯。

#### Scenario: 產出所有精彩片段的剪輯
- **WHEN** 使用者選擇 highlight 標籤，觸發精華剪輯產出
- **THEN** 系統篩選所有分類為 highlight 的片段，依時間順序合併為一部影片

### Requirement: 複合條件篩選
系統 SHALL 支援同時指定球員與標籤進行篩選。

#### Scenario: 產出球員 7 的進攻片段剪輯
- **WHEN** 使用者選擇球員 7 + offense 標籤
- **THEN** 系統篩選同時符合球員 7 且分類為 offense 的片段進行合併

### Requirement: FFmpeg 片段合併
系統 SHALL 使用 FFmpeg concat demuxer 合併片段，確保輸出影片播放流暢。

#### Scenario: 合併多個片段
- **WHEN** 系統合併 5 個片段為精華剪輯
- **THEN** 使用 FFmpeg concat demuxer 產出連續播放的 mp4 檔案

### Requirement: 精華剪輯中繼資料
系統 SHALL 記錄每部精華剪輯的中繼資料，包含篩選條件、包含的片段列表、總時長、檔案大小。

#### Scenario: 查詢精華剪輯列表
- **WHEN** 使用者查詢精華剪輯列表
- **THEN** 系統回傳所有精華剪輯，包含 id、篩選條件、片段數量、總時長、建立時間

### Requirement: 產出狀態追蹤
系統 SHALL 追蹤精華剪輯產出任務的狀態（pending → processing → completed/failed）。

#### Scenario: 產出完成
- **WHEN** FFmpeg 合併完成
- **THEN** 系統將狀態更新為 completed，記錄輸出檔案路徑與檔案大小
