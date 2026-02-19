## MODIFIED Requirements

### Requirement: 片段串流（含 Range 請求）
系統 SHALL 提供片段檔案串流端點，支援 HTTP Range 請求以實現時間軸跳轉。Range header MUST 經過驗證，無效的 Range（start < 0、start > end、end >= file_size、非數字）SHALL 回傳 416 Range Not Satisfiable。

#### Scenario: 完整串流
- **WHEN** 使用者請求串流片段（無 Range header）
- **THEN** 系統回傳完整片段檔案，包含 `Accept-Ranges: bytes` header

#### Scenario: Range 請求（時間軸跳轉）
- **WHEN** 使用者在播放器中點擊時間軸跳轉
- **THEN** 瀏覽器發送 Range 請求，系統回傳 206 Partial Content 與正確的位元組範圍

#### Scenario: 無效 Range header
- **WHEN** 請求包含無效的 Range header（負數 start、start > end、end >= file_size、非數字格式）
- **THEN** 系統 SHALL 回傳 416 Range Not Satisfiable，包含 Content-Range header 指示檔案總大小
