## ADDED Requirements

### Requirement: 從 YouTube 下載影片
系統 SHALL 接受 YouTube URL，透過 yt-dlp 下載影片至本機儲存。系統 SHALL 記錄影片來源資訊（URL、標題、時長）並追蹤下載狀態。

#### Scenario: 提交有效 YouTube URL
- **WHEN** 使用者提交一個有效的 YouTube 影片 URL
- **THEN** 系統建立下載任務，狀態設為 pending，並於背景開始下載

#### Scenario: 下載完成
- **WHEN** yt-dlp 成功下載影片
- **THEN** 系統將狀態更新為 completed，記錄檔案路徑、檔案大小與影片時長

#### Scenario: 下載失敗
- **WHEN** yt-dlp 下載過程發生錯誤（網路問題、URL 無效、影片不存在）
- **THEN** 系統將狀態更新為 failed，記錄錯誤訊息

#### Scenario: 提交無效 URL
- **WHEN** 使用者提交的 URL 非 YouTube 連結
- **THEN** 系統 SHALL 回傳驗證錯誤，不建立下載任務

### Requirement: 直接上傳影片檔案
系統 SHALL 支援直接上傳影片檔案作為次要的影片來源方式。

#### Scenario: 上傳有效影片檔案
- **WHEN** 使用者上傳 mp4/avi/mov/mkv 格式的影片檔案
- **THEN** 系統儲存檔案至 uploads 目錄，建立影片記錄，狀態直接設為 completed

#### Scenario: 上傳不支援的檔案格式
- **WHEN** 使用者上傳非影片格式的檔案
- **THEN** 系統 SHALL 拒絕上傳並回傳格式錯誤訊息

### Requirement: 影片列表與詳情
系統 SHALL 提供影片列表查詢與單一影片詳情查詢功能。

#### Scenario: 查詢影片列表
- **WHEN** 使用者請求影片列表
- **THEN** 系統回傳所有影片記錄，包含 id、標題、來源類型、狀態、時長、建立時間

#### Scenario: 查詢影片詳情
- **WHEN** 使用者請求特定影片的詳情
- **THEN** 系統回傳該影片的完整資訊，包含所有標記數量與片段數量

### Requirement: 刪除影片
系統 SHALL 支援刪除影片及其關聯的所有片段與標記資料。

#### Scenario: 刪除影片
- **WHEN** 使用者刪除一部影片
- **THEN** 系統刪除該影片的資料庫記錄、原始檔案、所有關聯的標記與片段檔案

### Requirement: 下載狀態追蹤
系統 SHALL 記錄每個下載任務的狀態轉換（pending → downloading → completed/failed）。

#### Scenario: 查詢下載進度
- **WHEN** 使用者查詢正在下載中的影片狀態
- **THEN** 系統回傳當前下載百分比與預估剩餘時間

### Requirement: 影片重新命名
系統 SHALL 支援修改影片標題。

#### Scenario: 更新影片標題
- **WHEN** 使用者提交新的影片標題
- **THEN** 系統更新該影片的 title 欄位並回傳更新後的影片資訊

#### Scenario: 空白標題
- **WHEN** 使用者提交空白標題
- **THEN** 系統 SHALL 回傳驗證錯誤，標題不可為空
