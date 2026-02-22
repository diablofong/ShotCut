# ShotCut

**籃球比賽影片標記與片段擷取工具**

上傳比賽影片，快速標記分類並自動剪輯出精華片段，分享給教練與家長。

---

## 功能特色

| 功能 | 說明 |
|------|------|
| 🎬 影片管理 | 支援本機上傳與 YouTube 連結匯入 |
| ⚡ 即時進度 | WebSocket 即時顯示下載進度 |
| 🏀 快速標記 | 播放中按數字鍵 1-3 即時標記進攻/防守/失誤 |
| 👤 球員標註 | 標記球員編號與姓名 |
| ✂️ 自動片段擷取 | FFmpeg 依標記自動切出影片片段 |
| 🎞️ 精華剪輯 | 依球員或分類自動合併產出精華影片 |
| 🔗 分享連結 | 產生限時分享連結（24h/7d/30d/永久） |
| 🔒 安全認證 | JWT + Refresh Token、角色權限控制 |

## 技術架構

| 層級 | 技術 |
|------|------|
| 前端 | React 19 + TypeScript + Vite + Tailwind CSS + Video.js |
| 後端 | Python 3.12 + FastAPI + SQLAlchemy (async) |
| 資料庫 | MariaDB 11 |
| 影片處理 | FFmpeg + yt-dlp |
| 部署 | Docker + Docker Compose |

## 快速連結

- [部署指南](deployment.md) — Docker 快速啟動
- [操作說明](usage.md) — 如何標記、切片、分享
- [API 參考](api.md) — 關鍵 API 端點
- [版本紀錄](changelog.md) — v1.0.0 更新內容

## 畫面預覽

完整操作示範請至 [GitHub](https://github.com/diablofong/ShotCut) 觀看。
