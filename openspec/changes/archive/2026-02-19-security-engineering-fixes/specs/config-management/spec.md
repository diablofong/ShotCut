## ADDED Requirements

### Requirement: Secret Key 強度驗證
系統 SHALL 在啟動時驗證 SECRET_KEY 環境變數的強度。Secret Key MUST 至少 32 字符，且不能使用常見的預設值（如 "change-me"、"test"、"secret"）。

#### Scenario: 啟動時檢查 Secret Key 長度
- **WHEN** 系統啟動並載入 SECRET_KEY 環境變數
- **THEN** 若 SECRET_KEY 少於 32 字符，系統 SHALL 拋出 ValueError 並拒絕啟動

#### Scenario: 拒絕預設 Secret Key
- **WHEN** SECRET_KEY 為 "change-me-to-a-random-string"、"test" 或 "secret"
- **THEN** 系統 SHALL 拋出 ValueError 並顯示「SECRET_KEY 不能使用預設值」

#### Scenario: 接受合格的 Secret Key
- **WHEN** SECRET_KEY 為至少 32 字符的隨機字串（如使用 `secrets.token_urlsafe(32)` 生成）
- **THEN** 系統正常啟動

#### Scenario: .env.example 包含強度要求說明
- **WHEN** 檢視 .env.example 檔案
- **THEN** SECRET_KEY 行 SHALL 包含註解說明：「必須至少 32 字符隨機字串，可用 python -c "import secrets; print(secrets.token_urlsafe(32))" 生成」

### Requirement: .env 檔案從 Git 移除
.env 檔案 MUST NOT 存在於 Git 儲存庫中，包含所有歷史 commits。已簽入的 .env 檔案 SHALL 使用 `git filter-branch` 或 BFG Repo-Cleaner 從歷史中完全移除。

#### Scenario: 檢查 Git 歷史無 .env
- **WHEN** 執行 `git log --all --full-history -- .env`
- **THEN** SHALL 無任何結果（檔案從未被追蹤）

#### Scenario: .gitignore 包含 .env
- **WHEN** 檢視 .gitignore 檔案
- **THEN** SHALL 包含 `.env` 規則，確保不被意外簽入

#### Scenario: 僅提供 .env.example
- **WHEN** 檢視專案根目錄
- **THEN** 存在 `.env.example` 作為範本，但無 `.env` 檔案簽入版本控制

#### Scenario: 生產環境密碼強度要求
- **WHEN** .env.example 包含密碼欄位（MYSQL_ROOT_PASSWORD、ADMIN_PASSWORD）
- **THEN** 預設值 SHALL 為強密碼範例（至少 16 字符，大小寫數字特殊符號混合）或明確標註 "CHANGE_THIS_IN_PRODUCTION"

### Requirement: 生產環境標誌
系統 SHALL 支援 IS_PRODUCTION 環境變數，用於區分開發和生產環境的不同安全設定。生產環境 SHALL 啟用嚴格的安全措施。

#### Scenario: IS_PRODUCTION 環境變數
- **WHEN** 設定 IS_PRODUCTION=true
- **THEN** 系統啟用：Cookie Secure Flag、嚴格的 CORS、HTTPS 強制重導向等生產安全措施

#### Scenario: 開發環境預設值
- **WHEN** IS_PRODUCTION 未設定或為 false
- **THEN** 系統允許較寬鬆的設定（如 Cookie Secure=False 允許 HTTP）

#### Scenario: 生產環境啟動檢查
- **WHEN** IS_PRODUCTION=true 且 SECRET_KEY 為弱密鑰
- **THEN** 系統 SHALL 拒絕啟動並顯示錯誤訊息
