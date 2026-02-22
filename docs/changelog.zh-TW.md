# 版本紀錄

## v1.0.0 — 2026-02-22

ShotCut 正式穩定版首次發布。

### 功能特色

- **影片管理** — 支援本機上傳與 YouTube 連結匯入（yt-dlp）
- **即時下載進度** — WebSocket 推送，斷線自動降級為 polling
- **軌道式快速標記** — 播放中按數字鍵 1-3 即時標記，拖曳色塊微調時間點
- **球員標註** — 每個標記可標記球員編號與姓名
- **自動片段擷取** — FFmpeg 依標記自動切出影片片段
- **個人精華剪輯** — 依球員或分類自動合併產出精華影片
- **分享連結** — 限時分享連結（24h/7d/30d/永久）
- **安全認證** — JWT Access Token + httpOnly Refresh Token Cookie
- **角色權限控制** — 管理員與一般使用者，資料完整隔離
- **播放速度控制** — 0.25x 至 2x

### 安全修復

| CVE | 套件 | 修復版本 |
|-----|------|---------|
| CVE-2025-62727 | starlette | 0.49.1 |
| CVE-2025-62611 | aiomysql | 0.3.0 |

其他安全改進：

- 以 `PyJWT` 取代 `python-jose`（漏洞修復）
- 以 `aiomysql` 取代 `asyncmy`（CVE-2025-62611）
- `python-multipart` 升級至 0.0.22（安全修復）
- `fastapi` 升級至 0.129.2
- 所有依賴套件鎖定為固定安全版本

### CI/CD

- 後端 CI：ruff 語法檢查 + pytest（23/23 測試通過）+ pip-audit + bandit + TruffleHog
- 前端 CI：ESLint + TypeScript 型別檢查 + npm audit（排除開發依賴）
