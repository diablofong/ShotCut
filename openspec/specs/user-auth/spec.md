## ADDED Requirements

### Requirement: 使用者帳號管理
系統 SHALL 提供使用者帳號管理功能，支援管理員（admin）與一般使用者（user）兩種角色。帳號僅能由管理員建立，不提供自行註冊功能。

#### Scenario: 系統首次啟動自動建立管理員帳號
- **WHEN** 系統首次啟動且資料庫中無任何管理員帳號
- **THEN** 系統自動從環境變數讀取 ADMIN_USERNAME 與 ADMIN_PASSWORD 建立初始管理員帳號

#### Scenario: 管理員建立新使用者帳號
- **WHEN** 管理員透過 POST /api/users 提供 username、password、display_name、role
- **THEN** 系統建立新使用者帳號，密碼以 bcrypt 雜湊儲存，回傳使用者資訊（不含密碼）

#### Scenario: 管理員停用使用者帳號
- **WHEN** 管理員透過 PUT /api/users/{id} 將 is_active 設為 false
- **THEN** 該使用者無法再登入，已簽發的 JWT 在驗證時被拒絕

#### Scenario: 一般使用者嘗試存取使用者管理 API
- **WHEN** 一般使用者嘗試存取 /api/users 端點
- **THEN** 系統回傳 403 Forbidden

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

### Requirement: 資源所有權與存取控制
系統 SHALL 實作資源所有權機制，確保一般使用者僅能存取自己建立的資源。

#### Scenario: 一般使用者上傳影片
- **WHEN** 一般使用者透過 POST /api/videos/upload 上傳影片
- **THEN** 系統將影片的 owner_id 設為該使用者的 id

#### Scenario: 一般使用者查看影片列表
- **WHEN** 一般使用者透過 GET /api/videos 查看影片列表
- **THEN** 系統僅回傳 owner_id 等於該使用者 id 的影片

#### Scenario: 管理員查看影片列表
- **WHEN** 管理員透過 GET /api/videos 查看影片列表
- **THEN** 系統回傳所有影片（包含所有使用者的影片及 owner_id 為 NULL 的舊資料）

#### Scenario: 一般使用者嘗試存取他人影片
- **WHEN** 一般使用者嘗試存取 owner_id 不屬於自己的影片
- **THEN** 系統回傳 403 Forbidden

#### Scenario: 一般使用者操作自己影片的標記與片段
- **WHEN** 一般使用者對自己的影片執行標記、分析、切片等操作
- **THEN** 系統允許操作，透過影片的 owner_id 追溯所有權

#### Scenario: 一般使用者產生精華剪輯
- **WHEN** 一般使用者透過 POST /api/highlights/generate 產生精華
- **THEN** 系統將精華的 owner_id 設為該使用者的 id，且僅使用該使用者擁有的影片片段

### Requirement: 分享連結免登入存取
系統 SHALL 維持分享連結的公開存取特性，持有 token 的任何人無需登入即可觀看分享內容。

#### Scenario: 訪客透過分享連結觀看精華
- **WHEN** 訪客透過 GET /api/shares/{token} 存取分享連結
- **THEN** 系統無需驗證身份，直接回傳精華剪輯內容並增加存取計數

#### Scenario: 一般使用者建立分享連結
- **WHEN** 一般使用者透過 POST /api/shares 建立分享連結
- **THEN** 系統驗證該精華剪輯屬於該使用者後，產生唯一 token 並回傳

### Requirement: 前端認證整合
系統 SHALL 在前端實作完整的認證流程，包含登入頁面、路由保護、JWT 自動附加與過期處理。

#### Scenario: 未登入使用者存取受保護頁面
- **WHEN** 未登入的使用者嘗試存取非公開頁面
- **THEN** 系統自動重導向至登入頁面

#### Scenario: 登入後存取系統
- **WHEN** 使用者成功登入
- **THEN** 系統將 JWT 儲存至 localStorage，後續所有 API 請求自動附加 Authorization header

#### Scenario: JWT 過期後操作
- **WHEN** API 回傳 401 狀態碼
- **THEN** 前端清除 localStorage 中的 token 並重導向至登入頁面

#### Scenario: 管理員存取使用者管理頁面
- **WHEN** 管理員導航至 /users 頁面
- **THEN** 系統顯示使用者管理介面，可新增、編輯、停用使用者帳號

### Requirement: CORS 來源控制
系統 SHALL 從環境變數 CORS_ORIGINS 讀取允許的跨域來源清單（逗號分隔），不得使用萬用字元 `*`。若環境變數未設定，預設僅允許同源請求。

#### Scenario: 設定允許的 CORS 來源
- **WHEN** 環境變數 CORS_ORIGINS 設為 "https://example.com,http://localhost:5173"
- **THEN** 系統僅允許來自這兩個 origin 的跨域請求

#### Scenario: 未設定 CORS_ORIGINS
- **WHEN** CORS_ORIGINS 環境變數不存在
- **THEN** 系統僅允許同源請求（空的 origin 清單）
