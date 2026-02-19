## MODIFIED Requirements

### Requirement: 影片管理頁面
前端 SHALL 提供影片管理頁面，顯示所有影片列表，支援新增（YouTube URL / 上傳）與刪除操作。下載中影片的 polling 機制 MUST 正確實作，不得因 useEffect 依賴陣列錯誤導致無限循環或重複建立定時器。

#### Scenario: 顯示影片列表
- **WHEN** 使用者進入影片管理頁面
- **THEN** 顯示所有影片的卡片列表，包含標題、來源類型、狀態、時長、標記數量

#### Scenario: 透過 YouTube URL 新增影片
- **WHEN** 使用者輸入 YouTube URL 並提交
- **THEN** 顯示下載進度，完成後影片出現在列表中

#### Scenario: 透過上傳新增影片
- **WHEN** 使用者選擇本機影片檔案並上傳
- **THEN** 顯示上傳進度，完成後影片出現在列表中

#### Scenario: 下載中影片的狀態輪詢
- **WHEN** 影片列表中有狀態為 pending 或 downloading 的影片
- **THEN** 前端啟動 polling 機制（每 2 秒），定時器 SHALL 不受 videos 狀態變更影響而重複建立
