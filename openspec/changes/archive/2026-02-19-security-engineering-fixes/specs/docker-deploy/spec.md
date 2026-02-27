## ADDED Requirements

### Requirement: 非 root 用戶運行容器
Docker 容器 MUST NOT 以 root 用戶運行應用程式。Dockerfile SHALL 創建專用的非特權用戶並切換至該用戶執行應用程式，以降低容器逃逸風險。

#### Scenario: 創建非 root 用戶
- **WHEN** 構建 Docker 映像
- **THEN** Dockerfile 在安裝依賴後 SHALL 創建 `shotcut` 群組和用戶

#### Scenario: 設定檔案所有權
- **WHEN** 應用程式檔案和資料目錄被複製到容器
- **THEN** 使用 `chown` 將所有權設定為 `shotcut:shotcut`

#### Scenario: 切換至非 root 用戶
- **WHEN** Dockerfile 執行 CMD 前
- **THEN** 使用 `USER shotcut` 指令切換用戶

#### Scenario: 容器內執行的進程
- **WHEN** 在運行中的容器內執行 `whoami`
- **THEN** 輸出 SHALL 為 `shotcut` 而非 `root`

#### Scenario: 容器逃逸風險降低
- **WHEN** 惡意程式碼在容器內執行
- **THEN** 因進程以非 root 運行，無法執行需要 root 權限的敏感操作

### Requirement: .dockerignore 檔案
專案 MUST 包含 `.dockerignore` 檔案，防止敏感檔案和不必要的檔案被複製到 Docker 映像中。

#### Scenario: 排除敏感檔案
- **WHEN** 構建 Docker 映像
- **THEN** `.env`、`.env.local`、Git 目錄等敏感檔案 SHALL NOT 被複製到映像

#### Scenario: 排除開發工具檔案
- **WHEN** 構建生產映像
- **THEN** `.vscode`、`.idea`、`*.md` 等開發工具檔案 SHALL NOT 包含在映像中

#### Scenario: 排除 node_modules 和 Python cache
- **WHEN** 構建映像
- **THEN** `node_modules`、`__pycache__`、`.pytest_cache` 等快取目錄 SHALL 被排除

#### Scenario: 排除資料目錄
- **WHEN** 構建映像
- **THEN** `data/` 目錄（資料庫、上傳檔案）SHALL NOT 包含在映像中

### Requirement: 資料庫埠不暴露到主機
docker-compose.yml MUST NOT 將資料庫埠（3306）暴露到主機網路。資料庫僅能在 Docker 網路內部訪問，防止外部直接連接。

#### Scenario: 資料庫埠僅內部訪問
- **WHEN** docker-compose.yml 定義資料庫服務
- **THEN** SHALL NOT 包含 `ports: - "3306:3306"` 配置

#### Scenario: 應用容器連接資料庫
- **WHEN** 後端容器需要連接資料庫
- **THEN** 使用內部 Docker 網路的服務名稱（如 `db:3306`）連接

#### Scenario: 主機無法直接連接資料庫
- **WHEN** 在主機上執行 `telnet localhost 3306`
- **THEN** 連接 SHALL 失敗（連接被拒絕）

#### Scenario: 開發環境需要外部訪問（可選）
- **WHEN** 開發者需要使用 GUI 工具連接資料庫
- **THEN** 可在本地 docker-compose.override.yml 中臨時加入埠對應，但不簽入版本控制

### Requirement: 基礎映像版本固定
Dockerfile 使用的基礎映像 SHALL 固定到特定版本標籤（包含主次修訂版本），避免意外的破壞性更新或安全問題。

#### Scenario: Python 基礎映像固定版本
- **WHEN** Dockerfile 定義基礎映像
- **THEN** 使用具體版本如 `python:3.11.8-slim` 而非 `python:3.11-slim` 或 `python:3-slim`

#### Scenario: Node 基礎映像固定版本
- **WHEN** 前端構建階段使用 Node 映像
- **THEN** 使用具體版本如 `node:20.11.0-slim` 而非 `node:20-slim`

#### Scenario: 定期更新基礎映像
- **WHEN** 每季度檢視基礎映像更新
- **THEN** 評估新版本的安全修復，更新 Dockerfile 中的版本標籤
