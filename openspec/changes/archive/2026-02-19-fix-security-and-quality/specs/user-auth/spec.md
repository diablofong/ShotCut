## MODIFIED Requirements

### Requirement: JWT 身份驗證
系統 SHALL 使用 JWT（JSON Web Token）進行身份驗證，採用 HS256 演算法簽名。SECRET_KEY MUST 從環境變數讀取，不得有硬編碼 fallback 預設值。若環境變數未設定，系統 SHALL 在啟動時拋出錯誤並拒絕啟動。

#### Scenario: 使用者以正確帳密登入
- **WHEN** 使用者透過 POST /api/auth/login 提交正確的 username 與 password
- **THEN** 系統回傳 JWT access_token、token_type 及使用者基本資訊（id、username、display_name、role）

#### Scenario: 使用者以錯誤帳密登入
- **WHEN** 使用者提交錯誤的 username 或 password
- **THEN** 系統回傳 401 Unauthorized，不揭露是帳號還是密碼錯誤

#### Scenario: 使用有效 JWT 存取受保護 API
- **WHEN** 請求 Authorization header 帶有有效的 Bearer token
- **THEN** 系統識別當前使用者並允許存取

#### Scenario: 使用過期或無效 JWT 存取受保護 API
- **WHEN** 請求帶有過期或被篡改的 JWT
- **THEN** 系統回傳 401 Unauthorized

#### Scenario: 未帶 JWT 存取受保護 API
- **WHEN** 請求未包含 Authorization header
- **THEN** 系統回傳 401 Unauthorized

#### Scenario: SECRET_KEY 環境變數未設定
- **WHEN** 系統啟動時 SECRET_KEY 環境變數不存在
- **THEN** 系統 SHALL 拋出錯誤並拒絕啟動

## ADDED Requirements

### Requirement: CORS 來源控制
系統 SHALL 從環境變數 CORS_ORIGINS 讀取允許的跨域來源清單（逗號分隔），不得使用萬用字元 `*`。若環境變數未設定，預設僅允許同源請求。

#### Scenario: 設定允許的 CORS 來源
- **WHEN** 環境變數 CORS_ORIGINS 設為 "https://example.com,http://localhost:5173"
- **THEN** 系統僅允許來自這兩個 origin 的跨域請求

#### Scenario: 未設定 CORS_ORIGINS
- **WHEN** CORS_ORIGINS 環境變數不存在
- **THEN** 系統僅允許同源請求（空的 origin 清單）
