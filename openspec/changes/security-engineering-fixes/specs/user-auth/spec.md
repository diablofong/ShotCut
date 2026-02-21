## MODIFIED Requirements

### Requirement: 前端認證整合
系統 SHALL 在前端實作完整的認證流程，包含登入頁面、路由保護、JWT 自動附加、Access Token 過期自動刷新與最終過期重導向。Access Token MUST NOT 儲存在 localStorage，以防止 XSS 攻擊竊取。Access Token SHALL 儲存在內存中（React Context/State），Refresh Token 由後端以 HttpOnly Cookie 提供。

#### Scenario: 未登入使用者存取受保護頁面
- **WHEN** 未登入的使用者嘗試存取非公開頁面
- **THEN** 系統自動重導向至登入頁面

#### Scenario: 登入後存取系統
- **WHEN** 使用者成功登入
- **THEN** 系統將 access_token 儲存至內存（React Context），Refresh Token 由後端自動設定為 HttpOnly Cookie，後續所有 API 請求自動附加 Authorization header

#### Scenario: Access Token 過期自動刷新
- **WHEN** API 回傳 401 狀態碼且 Refresh Token Cookie 有效
- **THEN** 前端自動換取新 access_token 並重試原始請求，使用者無感知

#### Scenario: 重試期間不重複 refresh
- **WHEN** 多個 API 請求同時收到 401
- **THEN** 前端僅發送一次 refresh 請求，所有 pending 請求等待 refresh 完成後一併重試

#### Scenario: Refresh Token 亦過期或撤銷
- **WHEN** Refresh Token 無效或過期導致 refresh 失敗
- **THEN** 前端清除內存中的 token 並重導向至登入頁面

#### Scenario: 頁面重新載入後的認證狀態
- **WHEN** 使用者重新載入頁面且 Refresh Token Cookie 仍有效
- **THEN** 前端自動呼叫 refresh 端點取得新 Access Token，恢復登入狀態

#### Scenario: 管理員存取使用者管理頁面
- **WHEN** 管理員導航至 /users 頁面
- **THEN** 系統顯示使用者管理介面，可新增、編輯、停用使用者帳號

#### Scenario: localStorage 不含任何 Token
- **WHEN** 檢查瀏覽器 localStorage
- **THEN** SHALL NOT 包含 `token`、`access_token`、`refresh_token` 等任何認證憑證

### Requirement: Refresh Token Cookie 安全設定
系統 SHALL 在設定 Refresh Token Cookie 時啟用所有安全標誌。Cookie Secure Flag MUST 在以下情況啟用：IS_PRODUCTION=true，或偵測到 `X-Forwarded-Proto: https` Header（反向代理場景）。所有環境 MUST 設定 `httpOnly=True` 和 `samesite="lax"`。

#### Scenario: 生產環境設定 Refresh Token Cookie
- **WHEN** 系統在生產環境（IS_PRODUCTION=true）設定 Refresh Token Cookie
- **THEN** Cookie 屬性 SHALL 包含：`httpOnly=True`、`secure=True`、`samesite="lax"`、`max_age=7天`

#### Scenario: 開發環境設定 Refresh Token Cookie
- **WHEN** 系統在開發環境（IS_PRODUCTION=false）且無反向代理時設定 Refresh Token Cookie
- **THEN** Cookie 屬性 SHALL 包含：`httpOnly=True`、`secure=False`、`samesite="lax"`、`max_age=7天`

#### Scenario: 透過反向代理 HTTPS 自動啟用 Secure Flag
- **WHEN** 請求包含 `X-Forwarded-Proto: https` Header（由 nginx/Caddy 等反向代理設定）
- **THEN** 系統 SHALL 自動啟用 Cookie Secure Flag，無論 IS_PRODUCTION 設定為何

#### Scenario: 透過 HTTPS 連接傳輸 Cookie
- **WHEN** 生產環境使用 HTTPS 連接（直接或透過反向代理）
- **THEN** Refresh Token Cookie 因 `secure=True` 僅透過加密連接傳輸

#### Scenario: JavaScript 無法存取 Refresh Token
- **WHEN** 惡意腳本嘗試透過 document.cookie 讀取 Cookie
- **THEN** 因 `httpOnly=True` 標誌，JavaScript 無法讀取 Refresh Token

## ADDED Requirements

### Requirement: 移除 Query Parameter Token 認證
系統 MUST NOT 接受透過 URL Query Parameter 傳遞的 Token 進行認證。所有認證 SHALL 僅接受 Authorization Header 或 HttpOnly Cookie。

#### Scenario: 嘗試透過 Query Parameter 傳遞 Token
- **WHEN** 請求 URL 包含 `?token=xxx` 參數
- **THEN** 系統 SHALL 忽略該參數，不用於認證

#### Scenario: WebSocket 連接認證
- **WHEN** 前端建立 WebSocket 連接
- **THEN** SHALL 依賴 Cookie 認證或在握手時透過 Header 傳遞 Token，NOT 在 URL 中

#### Scenario: 影片縮圖請求認證
- **WHEN** 前端請求影片縮圖 `/api/videos/{id}/thumbnail`
- **THEN** SHALL 使用 Authorization Header 或依賴 Cookie，NOT 使用 Query Parameter

#### Scenario: 片段下載認證
- **WHEN** 使用者下載片段 `/api/clips/{id}/download`
- **THEN** SHALL 使用 Authorization Header 或 Cookie，NOT 使用 Query Parameter

#### Scenario: 舊版 Query Token 相容性
- **WHEN** 系統檢測到使用 Query Parameter Token 的請求
- **THEN** 回傳 400 錯誤並提示「請使用 Authorization Header 進行認證」
