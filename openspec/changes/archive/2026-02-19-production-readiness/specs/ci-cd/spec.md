## ADDED Requirements

### Requirement: 後端 CI 工作流
GitHub Actions SHALL 在每次 push 或 pull_request 至任何分支時，自動執行後端 lint 與測試。

#### Scenario: Push 觸發後端 CI
- **WHEN** 任意分支有 git push
- **THEN** GitHub Actions 執行 ruff lint 與 pytest，在 Actions 頁面顯示結果

#### Scenario: Lint 失敗阻擋 CI
- **WHEN** ruff 發現程式碼風格錯誤
- **THEN** CI job 標記為 failed，不繼續執行測試

#### Scenario: 測試失敗阻擋 CI
- **WHEN** pytest 有測試案例失敗
- **THEN** CI job 標記為 failed，GitHub PR 顯示紅色 check

### Requirement: 前端 CI 工作流
GitHub Actions SHALL 在每次 push 或 pull_request 時，自動執行前端 ESLint 與 TypeScript 型別檢查。

#### Scenario: Push 觸發前端 CI
- **WHEN** 任意分支有 git push
- **THEN** GitHub Actions 執行 `eslint` 與 `tsc --noEmit`

#### Scenario: 型別錯誤阻擋 CI
- **WHEN** TypeScript 型別檢查發現錯誤
- **THEN** CI job 標記為 failed

### Requirement: CI 環境不依賴外部服務
CI 工作流 MUST 不需要 MariaDB 或其他外部服務即可執行，所有測試使用 SQLite in-memory。

#### Scenario: CI 無需資料庫服務
- **WHEN** GitHub Actions 執行後端測試
- **THEN** 無需啟動 MariaDB 容器，測試在純 Python 環境中完成
