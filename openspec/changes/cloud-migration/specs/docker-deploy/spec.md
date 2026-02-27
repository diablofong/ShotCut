## ADDED Requirements

### Requirement: 雲端開發環境（docker-compose.cloud.yml）
系統 SHALL 提供 `docker-compose.cloud.yml`，包含 MinIO service 模擬 Cloudflare R2，供本地開發測試 Presigned URL 流程使用。

#### Scenario: MinIO 模擬 R2 啟動
- **WHEN** 執行 `docker compose -f docker-compose.cloud.yml up`
- **THEN** MinIO service 啟動於 Port 9000（API）與 9001（Console），應用程式透過 S3-compatible API 連線

#### Scenario: 雲端模式不掛載影片 volume
- **WHEN** 使用 `docker-compose.cloud.yml` 啟動
- **THEN** app service MUST NOT 掛載 uploads/clips/highlights 目錄 volume，影片儲存完全交由 MinIO/R2 處理
