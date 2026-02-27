## ADDED Requirements

### Requirement: 檔案內容魔數驗證
影片上傳 SHALL 驗證檔案實際內容而非僅檢查副檔名。系統 MUST 讀取檔案前 262 bytes 進行魔數（Magic Number）檢查，確認 MIME 類型符合允許的影片格式。

#### Scenario: 上傳真實 MP4 影片
- **WHEN** 使用者上傳副檔名為 .mp4 且魔數為 `66 74 79 70` 的真實 MP4 檔案
- **THEN** 魔數驗證通過，系統開始處理上傳

#### Scenario: 上傳偽造副檔名的文字檔
- **WHEN** 使用者將 .txt 檔案改名為 .mp4 並上傳
- **THEN** 魔數檢查檢測到 MIME 類型為 text/plain，拒絕上傳並回傳 400 錯誤

#### Scenario: 支援的影片 MIME 類型
- **WHEN** 魔數檢查判定 MIME 類型
- **THEN** 僅接受：video/mp4、video/quicktime、video/x-msvideo、video/x-matroska

#### Scenario: 魔數檢查不影響正常檔案
- **WHEN** 上傳各種合法影片格式（MP4、MOV、AVI、MKV）
- **THEN** 所有格式皆通過魔數驗證

### Requirement: 檔案名稱清理與標準化
上傳的檔案名稱 MUST 經過清理，移除路徑遍歷字符、特殊符號、Unicode 正規化，防止檔案系統安全問題。

#### Scenario: 正常檔案名稱保留
- **WHEN** 使用者上傳檔案名稱為 "game-2024-02-21.mp4"
- **THEN** 檔案名稱保持不變

#### Scenario: 路徑遍歷嘗試
- **WHEN** 使用者上傳檔案名稱包含 "../" 或 "..\\"
- **THEN** 系統移除所有路徑分隔符，如 "../../secret.mp4" → "secret.mp4"

#### Scenario: 特殊字符替換
- **WHEN** 檔案名稱包含 `<>:"|?*` 等檔案系統不安全字符
- **THEN** 這些字符 SHALL 被替換為底線 "_"

#### Scenario: Unicode 正規化
- **WHEN** 檔案名稱包含全形字符或特殊 Unicode
- **THEN** 使用 NFKD 正規化處理

#### Scenario: 隱藏檔案防護
- **WHEN** 檔案名稱以點開頭（如 ".hidden.mp4"）
- **THEN** 移除開頭的點，變為 "hidden.mp4"

#### Scenario: 空檔案名稱處理
- **WHEN** 檔案名稱清理後為空
- **THEN** 使用預設名稱 "unnamed.mp4"
