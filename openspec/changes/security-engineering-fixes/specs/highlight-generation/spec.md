## ADDED Requirements

### Requirement: FFmpeg Concat 檔案路徑轉義
使用 FFmpeg concat demuxer 生成精華影片時，所有寫入 concat 檔案的片段路徑 MUST 經過適當轉義，防止特殊字符注入攻擊。

#### Scenario: 生成 concat 檔案前驗證路徑
- **WHEN** 系統準備生成精華影片，需要合併多個片段
- **THEN** 每個片段路徑 SHALL 先使用 validate_file_path() 驗證在 CLIP_DIR 內

#### Scenario: 路徑轉義防止注入
- **WHEN** 將片段路徑寫入 concat 暫存檔
- **THEN** 每個路徑 MUST 使用 shlex.quote() 轉義，格式為 `file 'escaped_path'\n`

#### Scenario: Concat 檔案範例
- **WHEN** 生成的 concat 檔案內容
- **THEN** 應類似：
  ```
  file '/app/clips/1/clip_1.mp4'
  file '/app/clips/2/clip_2.mp4'
  ```
  所有路徑以單引號包裹，特殊字符已轉義

#### Scenario: 檔案名稱包含特殊字符
- **WHEN** 片段路徑包含空格或引號
- **THEN** shlex.quote() SHALL 正確轉義，防止破壞 concat 檔案格式

#### Scenario: Concat 暫存檔安全
- **WHEN** 使用 tempfile.NamedTemporaryFile 創建 concat 檔案
- **THEN** 檔案 SHALL 使用 delete=False，在 FFmpeg 執行後手動刪除，避免資源洩露

### Requirement: 精華影片生成路徑安全
精華影片的輸出路徑 SHALL 使用資料庫 ID 構建，不得包含使用者可控的輸入。輸出路徑 MUST 在 HIGHLIGHT_DIR 範圍內。

#### Scenario: 輸出路徑使用資料庫 ID
- **WHEN** 生成精華影片的輸出路徑
- **THEN** 路徑 SHALL 為 `{HIGHLIGHT_DIR}/{highlight_id}/highlight.mp4`，僅使用整數 ID

#### Scenario: 驗證輸出目錄存在
- **WHEN** 準備生成精華影片
- **THEN** 若輸出目錄不存在，使用 os.makedirs() 創建，設定適當權限

#### Scenario: 輸出路徑在允許範圍內
- **WHEN** 構建輸出路徑後
- **THEN** 驗證 realpath 在 HIGHLIGHT_DIR 內
