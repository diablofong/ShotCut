## ADDED Requirements

### Requirement: 後端依賴漏洞掃描
CI/CD 管線 MUST 在測試階段後執行 Python 依賴漏洞掃描。掃描 SHALL 使用 `pip-audit` 工具，並在發現高嚴重性漏洞時使構建失敗。

#### Scenario: CI 執行依賴漏洞掃描
- **WHEN** 後端 CI workflow 執行到測試後階段
- **THEN** 系統執行 `pip-audit` 掃描所有依賴套件

#### Scenario: 發現高嚴重性漏洞
- **WHEN** `pip-audit` 檢測到高嚴重性（high/critical）漏洞
- **THEN** CI 構建 SHALL 失敗並在日誌中顯示漏洞詳情

#### Scenario: 無漏洞或僅有低嚴重性漏洞
- **WHEN** 掃描完成且無高嚴重性漏洞
- **THEN** CI 繼續執行後續步驟

#### Scenario: 本地開發環境漏洞檢查
- **WHEN** 開發者在本地執行 `pip-audit`
- **THEN** 工具顯示所有發現的漏洞及其嚴重性等級

### Requirement: 前端依賴漏洞掃描
CI/CD 管線 MUST 在前端測試後執行 npm 依賴漏洞掃描。掃描 SHALL 使用 `npm audit`，audit-level 設為 high，在發現高嚴重性漏洞時使構建失敗。

#### Scenario: CI 執行前端漏洞掃描
- **WHEN** 前端 CI workflow 執行到測試後階段
- **THEN** 系統執行 `npm audit --audit-level=high`

#### Scenario: 發現可自動修復的漏洞
- **WHEN** `npm audit` 檢測到可用 `npm audit fix` 修復的漏洞
- **THEN** CI 日誌 SHALL 建議執行修復命令

#### Scenario: 發現高嚴重性漏洞
- **WHEN** `npm audit` 檢測到 high 或 critical 級別漏洞
- **THEN** CI 構建 SHALL 失敗

#### Scenario: 定期更新依賴
- **WHEN** 專案每月檢查依賴更新
- **THEN** 開發者 SHALL 評估並更新有安全更新的套件

### Requirement: 靜態程式碼安全分析（SAST）
CI/CD 管線 SHALL 執行靜態程式碼安全分析，檢測常見安全漏洞模式。後端使用 `bandit` 工具，設定最小嚴重性等級為 medium（`-ll` 參數）。

#### Scenario: CI 執行 bandit 掃描
- **WHEN** 後端 CI workflow 執行安全掃描階段
- **THEN** 系統執行 `bandit -r backend/ -ll` 掃描所有後端程式碼

#### Scenario: 發現安全問題
- **WHEN** bandit 檢測到 medium 或 high 嚴重性問題
- **THEN** CI 構建 SHALL 失敗並顯示問題位置和建議修復方式

#### Scenario: 誤報處理
- **WHEN** bandit 報告的問題經確認為誤報
- **THEN** 開發者可在程式碼中加入 `# nosec` 註解並在 PR 中說明原因

#### Scenario: 掃描涵蓋範圍
- **WHEN** bandit 執行掃描
- **THEN** SHALL 涵蓋所有 backend/ 目錄下的 .py 檔案，包含 routers、services、models

### Requirement: 秘密掃描（Secret Scanning）
CI/CD 管線 MUST 執行秘密掃描，防止敏感資訊（API keys、密碼、tokens）被意外簽入。掃描 SHALL 使用 TruffleHog 或類似工具，檢查當前 commit 與 base branch 的差異。

#### Scenario: PR 觸發秘密掃描
- **WHEN** 開發者建立 Pull Request
- **THEN** CI 執行 TruffleHog 掃描 PR 中的所有變更

#### Scenario: 偵測到疑似秘密
- **WHEN** TruffleHog 在 commit 中發現高熵字串或已知秘密模式
- **THEN** CI 構建 SHALL 失敗並標示發現秘密的檔案和行數

#### Scenario: 測試用 mock 資料
- **WHEN** 程式碼包含明確標註為測試用的假資料（如 `test-api-key-not-real`）
- **THEN** 開發者可配置 TruffleHog 忽略規則

#### Scenario: 歷史 commit 掃描
- **WHEN** 執行一次性的完整儲存庫掃描
- **THEN** TruffleHog SHALL 檢查所有歷史 commits，識別過去洩露的秘密

### Requirement: 容器映像安全掃描
Docker 映像構建後 SHALL 執行安全漏洞掃描。掃描 SHALL 檢查基礎映像和已安裝套件的已知漏洞（CVE）。

#### Scenario: CI 構建 Docker 映像後掃描
- **WHEN** CI workflow 成功構建 Docker 映像
- **THEN** 執行容器掃描工具（如 Trivy、Grype）掃描映像

#### Scenario: 發現高嚴重性 CVE
- **WHEN** 映像掃描發現 HIGH 或 CRITICAL 級別的 CVE
- **THEN** CI SHALL 標記警告，建議更新基礎映像或套件

#### Scenario: 定期重新掃描已部署映像
- **WHEN** 新的 CVE 被公開
- **THEN** 生產環境的映像 SHALL 定期重新掃描，評估是否需要重新部署

#### Scenario: 映像標籤固定
- **WHEN** Dockerfile 使用基礎映像
- **THEN** SHALL 使用特定版本標籤（如 `python:3.11.8-slim`）而非浮動標籤（如 `python:3.11-slim`）

### Requirement: 依賴版本固定
專案依賴 SHALL 固定到特定版本，避免意外的破壞性更新。版本固定 MUST 包含主版本、次版本和修訂版本。

#### Scenario: Python requirements.txt 固定版本
- **WHEN** 檢查 backend/requirements.txt
- **THEN** 所有套件 SHALL 使用 `==` 固定到特定版本（如 `fastapi==0.115.6`）

#### Scenario: 避免使用範圍運算符
- **WHEN** 新增或更新依賴
- **THEN** 不得使用 `>=`、`~=` 等範圍運算符，除非有明確理由並註解說明

#### Scenario: npm package.json 鎖定版本
- **WHEN** 前端安裝新套件
- **THEN** package.json 使用固定版本，package-lock.json 鎖定完整依賴樹

#### Scenario: 定期更新固定版本
- **WHEN** 每季度檢視依賴更新
- **THEN** 評估安全更新、功能更新，測試後更新 requirements.txt 和 package.json
