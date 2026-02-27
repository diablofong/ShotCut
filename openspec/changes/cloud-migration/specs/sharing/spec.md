## ADDED Requirements

### Requirement: Feature Flag 控制分享功能
當 `ENABLE_SHARING=false` 時，分享連結功能模組 SHALL 整體停用，所有 `/shares` 端點（包含公開端點）MUST 拒絕請求。此機制透過 FastAPI router 層的 dependency 實作。

#### Scenario: 功能開關停用時拒絕所有分享請求
- **WHEN** 環境變數 `ENABLE_SHARING=false` 且使用者呼叫任何 `/api/shares` 端點（不論是否已登入）
- **THEN** 系統 SHALL 回傳 HTTP 404 與訊息「此功能未啟用」

#### Scenario: 功能開關預設為啟用
- **WHEN** 環境變數 `ENABLE_SHARING` 未設定
- **THEN** 所有 `/api/shares` 端點正常運作，行為與現有完全相同
