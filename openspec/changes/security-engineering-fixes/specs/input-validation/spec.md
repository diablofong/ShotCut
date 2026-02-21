## ADDED Requirements

### Requirement: 檔案上傳內容驗證
系統 SHALL 驗證所有上傳檔案的實際內容，不得僅依賴副檔名判斷。檔案類型驗證 MUST 使用魔數（Magic Number）檢查，讀取檔案前 262 bytes 判斷 MIME 類型。

#### Scenario: 上傳真實影片檔案
- **WHEN** 使用者上傳副檔名為 .mp4 且內容確實為 MP4 格式的檔案
- **THEN** 系統接受上傳並開始處理

#### Scenario: 上傳偽造副檔名的檔案
- **WHEN** 使用者上傳副檔名為 .mp4 但實際內容為文字檔的檔案
- **THEN** 系統拒絕上傳並回傳 400 錯誤，訊息為「檔案類型不符」

#### Scenario: 上傳支援的影片格式
- **WHEN** 使用者上傳 MIME 類型為 video/mp4、video/quicktime、video/x-msvideo 或 video/x-matroska 的檔案
- **THEN** 系統接受上傳

#### Scenario: 上傳不支援的檔案類型
- **WHEN** 使用者上傳 MIME 類型不在允許清單中的檔案
- **THEN** 系統拒絕上傳並回傳明確的錯誤訊息

### Requirement: 檔案名稱清理
系統 MUST 清理所有使用者提供的檔案名稱，防止路徑遍歷攻擊和特殊字符注入。檔案名稱 SHALL 經過 Unicode 正規化、移除路徑分隔符、僅保留安全字符。

#### Scenario: 正常檔案名稱
- **WHEN** 使用者上傳檔案名稱為 "basketball-game.mp4"
- **THEN** 系統保留原始檔案名稱

#### Scenario: 包含路徑遍歷的檔案名稱
- **WHEN** 使用者上傳檔案名稱為 "../../etc/passwd.mp4"
- **THEN** 系統清理為 "etcpasswd.mp4"，移除所有路徑分隔符

#### Scenario: 包含特殊字符的檔案名稱
- **WHEN** 使用者上傳檔案名稱包含非字母數字字符（如 `<>:"|?*`）
- **THEN** 系統將特殊字符替換為底線 "_"

#### Scenario: 隱藏檔案名稱（以點開頭）
- **WHEN** 使用者上傳檔案名稱為 ".hidden.mp4"
- **THEN** 系統移除開頭的點，清理為 "hidden.mp4"

#### Scenario: 空檔案名稱或僅含無效字符
- **WHEN** 使用者上傳的檔案名稱清理後為空
- **THEN** 系統使用預設名稱 "unnamed"

### Requirement: FFmpeg 命令路徑驗證
系統 MUST 在調用 FFmpeg 前驗證所有檔案路徑，防止命令注入攻擊。路徑驗證 SHALL 確保檔案路徑在允許的目錄內，使用 realpath 解析符號連結。

#### Scenario: 使用資料庫中的合法影片路徑
- **WHEN** 系統從資料庫讀取影片路徑並調用 FFmpeg
- **THEN** 在執行 FFmpeg 前，系統先驗證路徑在 UPLOAD_DIR 內

#### Scenario: 路徑遍歷嘗試
- **WHEN** 檔案路徑經過符號連結後指向允許目錄外的位置
- **THEN** 路徑驗證失敗，系統拒絕執行 FFmpeg 並回傳 404 錯誤

#### Scenario: FFmpeg concat 模式路徑轉義
- **WHEN** 生成精華影片使用 concat demuxer，需要將多個片段路徑寫入文字檔
- **THEN** 每個檔案路徑 MUST 使用 shlex.quote() 轉義，防止特殊字符注入

#### Scenario: 所有 FFmpeg 路徑參數驗證
- **WHEN** 任何 FFmpeg 命令包含檔案路徑參數（input、output、concat file）
- **THEN** 系統 SHALL 對所有路徑參數執行驗證，確保在允許目錄內

### Requirement: 資料庫參數化查詢
系統 SHALL 使用 SQLAlchemy ORM 的參數化查詢，不得使用字符串拼接構建 SQL 查詢。所有動態查詢條件 MUST 通過 ORM 方法或綁定參數傳遞。

#### Scenario: 使用 ORM 查詢使用者
- **WHEN** 系統需要根據 username 查詢使用者
- **THEN** 使用 `select(User).where(User.username == value)` 而非字符串拼接

#### Scenario: 動態篩選條件
- **WHEN** API 接受多個可選篩選參數
- **THEN** 使用 ORM 的 `.where()` 方法逐步添加條件，保持參數化

#### Scenario: 原生 SQL 查詢（如需使用）
- **WHEN** 必須執行原生 SQL 查詢
- **THEN** 使用 text() 函數配合綁定參數，不得直接拼接變數
