## Context

ShotCut 目前為本地部署，影片存於應用程式伺服器本地磁碟，使用者需在同一網路環境才能存取。為支援遠端使用場景（教練與球員在家觀看），需將系統遷移至雲端。

**當前狀態**：
- 影片存於本地 `uploads/` 目錄
- 串流透過 FastAPI FileResponse 回傳，佔用伺服器頻寬
- 前端直接 multipart POST 影片至後端，大型影片佔用記憶體
- 切片、精華、分享功能在雲端環境缺乏實用性

**約束條件**：
- 完全免費（Oracle Cloud Always Free + Cloudflare Free）
- 使用人數僅 2 人，資源需求極低
- 必須向後相容（STORAGE_BACKEND=local 維持原有行為）
- 雲端版不需要切片、精華、分享功能

**相關方**：
- 開發團隊：實施遷移
- 使用者（2 人）：需重新上傳影片至雲端儲存

## Goals / Non-Goals

**Goals:**
- 影片儲存遷移至 Cloudflare R2（10GB 免費）
- 前端直接透過 Presigned PUT 上傳影片至 R2
- 串流改為 302 redirect 至 R2 Presigned GET URL
- 新增 Feature Flag 系統控制功能模組啟用狀態
- 本地開發使用 MinIO 模擬 R2

**Non-Goals:**
- 不重構現有標記（Mark）功能
- 不改變 JWT 認證機制
- 不遷移資料庫（保留 MariaDB）
- 不實作自動影片過期清理（後續版本）
