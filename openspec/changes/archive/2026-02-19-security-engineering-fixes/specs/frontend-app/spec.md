## MODIFIED Requirements

### Requirement: Token 安全儲存與傳遞
前端應用程式 MUST NOT 將 Access Token 儲存在 localStorage 或 sessionStorage，以防止 XSS 攻擊竊取。Access Token SHALL 儲存在內存中（React Context/State），所有 API 請求 MUST 透過 Authorization Header 傳遞 Token。

#### Scenario: Token 儲存在 React Context
- **WHEN** 使用者成功登入
- **THEN** Access Token 儲存在 AuthContext 的 state 中，Refresh Token 由後端設定為 HttpOnly Cookie

#### Scenario: localStorage 不含 Token
- **WHEN** 檢查瀏覽器開發者工具的 localStorage
- **THEN** SHALL NOT 包含任何認證相關的 key（token、access_token、refresh_token 等）

#### Scenario: API 請求自動附加 Authorization Header
- **WHEN** 前端透過 axios 發送 API 請求
- **THEN** axios interceptor 自動從 Context 讀取 Token 並加入 `Authorization: Bearer {token}` header

#### Scenario: 頁面重新載入後的認證狀態
- **WHEN** 使用者重新載入頁面
- **THEN** 前端自動呼叫 `/api/auth/refresh` 使用 HttpOnly Cookie 取得新 Access Token

#### Scenario: WebSocket 連接不在 URL 中傳遞 Token
- **WHEN** 前端建立 WebSocket 連接
- **THEN** SHALL 依賴 Cookie 認證，NOT 在 WebSocket URL 中加入 `?token=xxx`

### Requirement: 移除 URL 參數中的 Token
所有需要認證的資源請求（影片縮圖、片段下載、精華下載）MUST NOT 在 URL Query Parameter 中傳遞 Token。

#### Scenario: 影片縮圖請求
- **WHEN** 前端顯示影片縮圖
- **THEN** 使用 `<img src="/api/videos/{id}/thumbnail" />` 依賴 Cookie，NOT `?token=xxx`

#### Scenario: 片段下載連結
- **WHEN** 使用者點擊下載片段按鈕
- **THEN** 使用 fetch API 配合 Authorization Header 下載，NOT 直接 `<a href="...?token=xxx">`

#### Scenario: 精華下載連結
- **WHEN** 使用者下載精華影片
- **THEN** 透過 fetch 請求配合 Authorization Header，下載後使用 Blob URL

#### Scenario: 瀏覽器歷史記錄無 Token
- **WHEN** 檢查瀏覽器歷史記錄
- **THEN** 所有 URL SHALL NOT 包含 token 參數

### Requirement: XSS 防護最佳實踐
React 應用程式 SHALL 遵循 XSS 防護最佳實踐，避免使用 dangerouslySetInnerHTML，所有使用者輸入透過 React 自動轉義渲染。

#### Scenario: 無 dangerouslySetInnerHTML 使用
- **WHEN** 檢查所有 React 元件
- **THEN** SHALL NOT 使用 `dangerouslySetInnerHTML` 屬性

#### Scenario: 使用者輸入自動轉義
- **WHEN** 顯示使用者輸入的影片標題、標籤
- **THEN** 使用 `{video.title}` 等 JSX 語法，React 自動轉義 HTML 特殊字符

#### Scenario: URL 參數驗證
- **WHEN** 從 URL 參數讀取資料（如 share token）
- **THEN** 驗證格式後再使用，不直接渲染到 DOM

### Requirement: 依賴套件安全更新
前端專案 SHALL 定期更新依賴套件，修復已知的安全漏洞。npm audit 發現的高嚴重性漏洞 SHALL 優先處理。

#### Scenario: 修復 minimatch ReDoS 漏洞
- **WHEN** npm audit 報告 minimatch < 10.2.1 漏洞
- **THEN** 執行 `npm audit fix` 或手動更新到安全版本

#### Scenario: 修復 ajv ReDoS 漏洞
- **WHEN** npm audit 報告 ajv < 8.18.0 漏洞
- **THEN** 更新 ajv 或相關依賴到安全版本

#### Scenario: 定期執行 npm audit
- **WHEN** 每月檢查依賴安全性
- **THEN** 執行 `npm audit` 並評估建議的修復
