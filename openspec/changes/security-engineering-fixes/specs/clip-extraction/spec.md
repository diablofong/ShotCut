## ADDED Requirements

### Requirement: FFmpeg 路徑驗證防止命令注入
所有傳遞給 FFmpeg 的檔案路徑 MUST 經過驗證，確保路徑在允許的目錄範圍內，防止命令注入攻擊。驗證 SHALL 使用 realpath 解析符號連結。

#### Scenario: 驗證影片檔案路徑
- **WHEN** 系統從資料庫讀取影片路徑並準備調用 FFmpeg
- **THEN** 在執行 FFmpeg 前，SHALL 使用 validate_file_path() 確認路徑在 UPLOAD_DIR 內

#### Scenario: 驗證輸出檔案路徑
- **WHEN** 系統生成片段的輸出路徑
- **THEN** 輸出路徑 SHALL 在 CLIP_DIR 內，使用資料庫 ID 構建，不使用使用者輸入

#### Scenario: 符號連結解析
- **WHEN** 檔案路徑包含符號連結
- **THEN** validate_file_path() 使用 os.path.realpath() 解析後再檢查

#### Scenario: 路徑遍歷嘗試被阻止
- **WHEN** 檔案路徑經過 realpath 後指向允許目錄外
- **THEN** 驗證失敗，拋出 HTTPException 404

#### Scenario: 所有 FFmpeg 參數驗證
- **WHEN** FFmpeg 命令包含 -i input、-ss、-t、output 等參數
- **THEN** 所有涉及檔案路徑的參數（input、output）SHALL 經過驗證

### Requirement: FFmpeg 參數安全傳遞
FFmpeg 命令參數 SHALL 使用列表形式傳遞給 subprocess.run()，不得使用 shell=True。時間參數 SHALL 轉換為字串前驗證為數值類型。

#### Scenario: 使用列表而非字串命令
- **WHEN** 調用 subprocess.run() 執行 FFmpeg
- **THEN** 命令 SHALL 以列表形式傳遞（如 `["ffmpeg", "-i", path]`），不使用 shell=True

#### Scenario: 時間參數驗證
- **WHEN** start_time 和 duration 從資料庫讀取
- **THEN** 轉換為字串前 SHALL 驗證為 float 類型，防止注入

#### Scenario: 固定參數使用
- **WHEN** 構建 FFmpeg 命令
- **THEN** 使用固定參數（如 "-c copy", "-avoid_negative_ts make_zero"），不插入動態值

#### Scenario: FFmpeg 超時設定
- **WHEN** 執行 FFmpeg 命令
- **THEN** subprocess.run() SHALL 包含 timeout 參數，防止無限執行
