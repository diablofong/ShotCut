## MODIFIED Requirements

### Requirement: 模組化 Docker Compose

系統 SHALL 提供模組化的 Docker Compose 結構，分為模組層（工程師用）與 Preset 層（使用者用）。

#### Scenario: 使用 selfhosted preset 啟動

- **WHEN** 執行 `docker compose -f docker-compose.selfhosted.yml up`
- **THEN** app、MariaDB、MinIO 一併啟動；app 等待 DB/MinIO health check 通過後才啟動；首次執行自動建 bucket、DB schema、管理員帳號

#### Scenario: 使用 cloud preset 啟動

- **WHEN** 執行 `docker compose -f docker-compose.cloud.yml up`
- **THEN** 僅啟動 app service，DATABASE_URL 與 S3_* 從 .env 讀取，指向外部服務

#### Scenario: 資料持久化

- **WHEN** 執行 `docker compose down` 再 `up`
- **THEN** MariaDB 資料（`./data/db` bind mount）與 MinIO 資料（`./data/minio` bind mount）不丟失；資料存放於專案目錄下，便於備份與搬移

#### Scenario: MinIO Console 不在生產環境外露

- **WHEN** 使用 `docker-compose.selfhosted.yml` 或 `docker-compose.cloud.yml`
- **THEN** MinIO port 9001 MUST NOT 對外 expose；僅 `docker-compose.dev.yml` 開放 9001

#### Scenario: Restart policy

- **WHEN** app service 意外崩潰
- **THEN** `restart: unless-stopped` 自動重啟

### Requirement: 環境變數設計

selfhosted preset SHALL 自動組裝 `DATABASE_URL` 與 `S3_ENDPOINT_URL`，使用者只需填：`S3_ACCESS_KEY_ID`、`S3_SECRET_ACCESS_KEY`、`S3_BUCKET_NAME`（預設 `shotcut`）、`DB_PASSWORD`、`SECRET_KEY`。

MinIO SHALL 直接使用 `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` 作為 `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`，不需要額外變數。`S3_SECRET_ACCESS_KEY` 長度 MUST >= 8 字元（MinIO 要求）。
