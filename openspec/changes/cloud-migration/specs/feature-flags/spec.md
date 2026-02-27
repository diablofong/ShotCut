## ADDED Requirements

### Requirement: 功能開關（Feature Flags）
系統 SHALL 支援透過環境變數控制功能模組的啟用與停用。功能開關 MUST 在應用程式啟動時由 `Settings` 類別統一讀取，各 router MUST 在處理請求前檢查對應開關。開關預設值 MUST 為 `true`（向後相容，不影響現有部署）。

#### Scenario: 功能開關停用時拒絕切片請求
- **WHEN** 環境變數 `ENABLE_CLIPS=false` 且使用者呼叫任何 `/clips` 端點
- **THEN** 系統 SHALL 回傳 HTTP 404 與訊息「此功能未啟用」

#### Scenario: 功能開關停用時拒絕精華請求
- **WHEN** 環境變數 `ENABLE_HIGHLIGHTS=false` 且使用者呼叫任何 `/highlights` 端點
- **THEN** 系統 SHALL 回傳 HTTP 404 與訊息「此功能未啟用」

#### Scenario: 功能開關停用時拒絕分享請求
- **WHEN** 環境變數 `ENABLE_SHARING=false` 且使用者呼叫任何 `/shares` 端點
- **THEN** 系統 SHALL 回傳 HTTP 404 與訊息「此功能未啟用」

#### Scenario: 功能開關預設為啟用
- **WHEN** 環境變數 `ENABLE_CLIPS`、`ENABLE_HIGHLIGHTS`、`ENABLE_SHARING` 均未設定
- **THEN** 所有功能正常運作，與現有行為相同

#### Scenario: 功能開關啟用時正常處理
- **WHEN** 環境變數 `ENABLE_CLIPS=true` 且使用者呼叫 `/clips` 端點
- **THEN** 系統正常處理請求，功能開關不影響回應
