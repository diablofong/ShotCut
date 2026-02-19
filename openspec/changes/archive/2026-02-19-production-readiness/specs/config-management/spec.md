## ADDED Requirements

### Requirement: 集中化設定類別
所有環境變數 MUST 透過單一 `Settings` 類別（pydantic-settings `BaseSettings`）存取，位於 `backend/config.py`。

#### Scenario: 啟動時驗證必填設定
- **WHEN** 應用程式啟動（`uvicorn` 啟動）
- **THEN** pydantic-settings 自動驗證所有必填環境變數（`DATABASE_URL`、`SECRET_KEY`）；若缺少則拋出 `ValidationError` 並中止啟動

#### Scenario: 設定為 singleton
- **WHEN** 任何模組呼叫 `get_settings()`
- **THEN** 回傳同一個 `Settings` 實例（透過 `@lru_cache` 快取），不重複讀取環境變數

### Requirement: 型別安全的設定存取
所有設定欄位 MUST 有明確型別定義，數值型別（int、bool）自動從環境變數字串轉換。

#### Scenario: 整數型別轉換
- **WHEN** 環境變數 `JWT_ACCESS_EXPIRE_MINUTES=15`
- **THEN** `settings.jwt_access_expire_minutes` 為 Python `int` 值 `15`，不需要手動 `int(os.getenv(...))`

#### Scenario: 必填項目缺失
- **WHEN** `SECRET_KEY` 環境變數未設定
- **THEN** 應用程式啟動失敗，日誌明確顯示缺少哪個設定項目

### Requirement: 不再直接使用 os.getenv
後端所有模組 MUST 改用 `get_settings()` 取得設定，`os.getenv()` 僅保留在 `backend/config.py` 中。

#### Scenario: 設定從 config 模組取得
- **WHEN** 任意後端模組需要讀取環境變數（如 DATABASE_URL、SECRET_KEY）
- **THEN** 透過 `from backend.config import get_settings; settings = get_settings()` 取得，不直接呼叫 `os.getenv()`
