## Purpose

透過 StorageService 抽象層統一管理影片與縮圖的儲存，支援本地檔案系統（開發）與 Cloudflare R2（雲端）兩種後端，前端直接使用 Presigned URL 上傳/串流影片，不佔用應用程式伺服器頻寬。

## Requirements
