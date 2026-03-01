## Context

ShotCut 1.x 有 local 和 S3 兩套儲存路徑，導致程式碼分裂、雙重維護、前端需 build-time env。

**2.0 目標**：統一為 S3-compatible 單一路徑，自建版 = 雲端版（同程式碼、同 image、不同 .env）。

**Phase A~F（已完成）**：StorageService 抽象層、Presigned PUT 上傳、302 redirect 串流、Feature Flag、安全修補。

**Phase G0/G/H（進行中）**：移除 local 後端、統一 S3_* 命名、runtime config、模組化 Docker Compose、資安補強。

## Goals / Non-Goals

**Goals:**
- 移除 `LocalStorageService`，統一走 S3-compatible
- `R2_*` env → `S3_*`（向後相容 validator）
- 前端 runtime `GET /api/config`，移除 build-time `VITE_*`
- 模組化 docker-compose + selfhosted/cloud preset
- Graceful shutdown、startup 清理、security headers

**Non-Goals:**
- 不重構標記功能，不改 JWT 認證
- 不加 PostgreSQL（2.1 再評估）
- 不加 Cloudflare Pages（同容器部署）
