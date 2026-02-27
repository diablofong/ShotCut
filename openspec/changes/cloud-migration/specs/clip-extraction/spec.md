## ADDED Requirements

### Requirement: Feature Flag 控制片段功能
當 `ENABLE_CLIPS=false` 時，片段功能模組 SHALL 整體停用，所有 `/clips` 端點 MUST 拒絕請求。此機制透過 FastAPI router 層的 dependency 實作，與業務邏輯解耦。

#### Scenario: 功能開關停用時拒絕所有切片請求
- **WHEN** 環境變數 `ENABLE_CLIPS=false` 且使用者呼叫任何 `/api/clips` 端點（不論 HTTP method）
- **THEN** 系統 SHALL 回傳 HTTP 404 與訊息「此功能未啟用」，不執行任何 FFmpeg 操作

#### Scenario: 功能開關預設為啟用
- **WHEN** 環境變數 `ENABLE_CLIPS` 未設定
- **THEN** 所有 `/api/clips` 端點正常運作，行為與現有完全相同
