## ADDED Requirements

### Requirement: Refresh Token 機制
系統 SHALL 支援 Access Token + Refresh Token 雙 token 策略，以縮短 Access Token 有效期同時維持使用者登入狀態。

#### Scenario: 登入取得 Refresh Token
- **WHEN** 使用者透過 POST `/api/auth/login` 成功登入
- **THEN** 系統除原有 `access_token` 外，額外以 httpOnly Cookie（`refresh_token`）回傳 Refresh Token；Refresh Token 有效期 7 天

#### Scenario: 使用 Refresh Token 換取新 Access Token
- **WHEN** 前端呼叫 POST `/api/auth/refresh`，Cookie 含有效 `refresh_token`
- **THEN** 系統驗證 Refresh Token 有效性，回傳新的 `access_token`（有效期 15 分鐘）；若 Refresh Token 無效或已過期，回傳 401

#### Scenario: 登出撤銷 Refresh Token
- **WHEN** 使用者呼叫 POST `/api/auth/logout`
- **THEN** 系統將資料庫中對應 Refresh Token 標記為 revoked，並清除 Cookie

#### Scenario: 已撤銷的 Refresh Token 無法使用
- **WHEN** 前端使用已被撤銷的 refresh_token 呼叫 `/api/auth/refresh`
- **THEN** 系統回傳 401 Unauthorized

### Requirement: 前端自動 Token Refresh
前端 axios interceptor MUST 在 Access Token 過期時（收到 401）自動呼叫 `/api/auth/refresh` 換取新 token，對使用者透明。

#### Scenario: Access Token 過期自動刷新
- **WHEN** API 請求收到 401 回應
- **THEN** 前端自動 POST `/api/auth/refresh`；若成功，以新 access_token 重試原始請求；若失敗（Refresh Token 無效），重導向至登入頁面

#### Scenario: 重試期間不重複 refresh
- **WHEN** 多個 API 請求同時收到 401
- **THEN** 前端僅發送一次 refresh 請求，所有 pending 請求等待 refresh 完成後一併重試

## MODIFIED Requirements

### Requirement: JWT 身份驗證
系統 SHALL 使用 JWT（JSON Web Token）進行身份驗證，採用 HS256 演算法簽名。SECRET_KEY MUST 從環境變數讀取，不得有硬編碼 fallback 預設值。若環境變數未設定，系統 SHALL 在啟動時拋出錯誤並拒絕啟動。Access Token 有效期 MUST 縮短為 15 分鐘（由 `JWT_ACCESS_EXPIRE_MINUTES` 環境變數控制，預設 15）。

#### Scenario: 使用者以正確帳密登入
- **WHEN** 使用者透過 POST /api/auth/login 提交正確的 username 與 password
- **THEN** 系統回傳 `access_token`（有效期 15 分鐘）、`token_type`、使用者基本資訊，並以 httpOnly Cookie 設定 `refresh_token`（有效期 7 天）

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

## MODIFIED Requirements

### Requirement: 前端認證整合
系統 SHALL 在前端實作完整的認證流程，包含登入頁面、路由保護、JWT 自動附加、Access Token 過期自動刷新與最終過期重導向。

#### Scenario: 未登入使用者存取受保護頁面
- **WHEN** 未登入的使用者嘗試存取非公開頁面
- **THEN** 系統自動重導向至登入頁面

#### Scenario: 登入後存取系統
- **WHEN** 使用者成功登入
- **THEN** 系統將 access_token 儲存至 localStorage，後續所有 API 請求自動附加 Authorization header

#### Scenario: Access Token 過期自動刷新
- **WHEN** API 回傳 401 狀態碼且 Refresh Token Cookie 有效
- **THEN** 前端自動換取新 access_token 並重試原始請求，使用者無感知

#### Scenario: Refresh Token 亦過期或撤銷
- **WHEN** Refresh Token 無效或過期導致 refresh 失敗
- **THEN** 前端清除 localStorage 中的 token 並重導向至登入頁面

#### Scenario: 管理員存取使用者管理頁面
- **WHEN** 管理員導航至 /users 頁面
- **THEN** 系統顯示使用者管理介面，可新增、編輯、停用使用者帳號
