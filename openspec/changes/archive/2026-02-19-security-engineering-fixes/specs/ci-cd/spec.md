## ADDED Requirements

### Requirement: CI/CD 安全掃描整合
CI/CD 管線 SHALL 在測試後階段執行全面的安全掃描，包含依賴漏洞、靜態程式碼分析、秘密掃描。任何高嚴重性問題 SHALL 導致構建失敗。

#### Scenario: 後端 CI 執行安全掃描步驟
- **WHEN** 後端 CI workflow 在測試通過後執行
- **THEN** SHALL 依序執行：pip-audit（依賴掃描）、bandit（SAST）、TruffleHog（秘密掃描）

#### Scenario: 前端 CI 執行安全掃描步驟
- **WHEN** 前端 CI workflow 在測試通過後執行
- **THEN** SHALL 依序執行：npm audit（依賴掃描）、TruffleHog（秘密掃描）

#### Scenario: 安全掃描發現問題
- **WHEN** 任一安全掃描工具偵測到高嚴重性問題
- **THEN** CI 構建 SHALL 失敗，並在 GitHub Actions 日誌中顯示詳細問題

#### Scenario: CI 通知安全問題
- **WHEN** 安全掃描失敗
- **THEN** GitHub Pull Request Checks SHALL 標示為失敗，阻止合併

### Requirement: 秘密掃描防止洩露
CI SHALL 使用 TruffleHog 或類似工具掃描所有 commits，防止 API keys、密碼、tokens 被意外簽入。掃描 SHALL 檢查當前 PR 的所有變更。

#### Scenario: PR 自動執行秘密掃描
- **WHEN** 開發者提交 Pull Request
- **THEN** CI 自動執行 TruffleHog 掃描 PR 中的所有 commits

#### Scenario: 偵測到高熵字串
- **WHEN** Commit 包含高熵字串（如隨機生成的 API key）
- **THEN** TruffleHog 標記為潛在秘密，CI 構建失敗

#### Scenario: 掃描涵蓋所有檔案類型
- **WHEN** TruffleHog 執行
- **THEN** SHALL 掃描 .py、.js、.ts、.env.example、.yml 等所有文字檔案

### Requirement: 定期安全審查
專案 SHALL 定期執行自動化安全審查，即使無新 commits 也應檢查依賴更新和新發現的 CVE。

#### Scenario: 每週執行依賴掃描
- **WHEN** 每週一觸發排程 workflow
- **THEN** 執行 pip-audit 和 npm audit，檢查是否有新的漏洞公告

#### Scenario: 發現新漏洞通知
- **WHEN** 定期掃描發現新的高嚴重性漏洞
- **THEN** GitHub Actions SHALL 建立 Issue 通知維護者

