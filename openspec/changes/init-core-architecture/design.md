## Context

ShotCut 是一款籃球比賽影片標記與片段擷取工具，目前專案僅有空白骨架結構。使用者（籃球教練）將比賽影片上傳至 YouTube，需要一個工具能下載這些影片、自動偵測關鍵時刻、標記分類、切出片段並產出個人精華剪輯，最終分享給家長。

現有狀態：
- 後端：空的 Python 模組結構 + requirements.txt（fastapi、uvicorn、ffmpeg-python 等）
- 前端：空的目錄結構，無任何設定檔或程式碼
- 無資料庫、無 Docker 配置

約束條件：
- 影片來源以 YouTube 下載為主（使用者自己上傳的影片）
- 資料庫必須使用 MariaDB
- 最終需 Docker 容器化部署
- 影片處理為 CPU 密集操作，需背景任務處理

## Goals / Non-Goals

**Goals:**
- 建立可運行的全端應用，涵蓋從影片取得到分享的完整流程
- 使用 Docker + docker-compose 實現一鍵部署
- 使用 MariaDB + SQLAlchemy async 作為持久化層
- 提供直覺的影片標記操作介面
- 支援背景任務處理耗時操作（下載、分析、切片、合併）

**Non-Goals:**
- 即時多人協作標記
- 雲端物件儲存（S3 等，初版使用本機檔案系統）
- 行動裝置原生 App
- AI 自動辨識球員或戰術（列入未來規劃，見 Future 章節）

## Decisions

### 1. 資料庫：MariaDB + SQLAlchemy async + asyncmy

**選擇：** MariaDB 搭配 SQLAlchemy 2.0 async 模式，asyncmy 作為驅動

**替代方案：**
- SQLite + aiosqlite：輕量但不支援並發寫入，Docker 環境下檔案鎖定不穩定
- PostgreSQL + asyncpg：功能更強但使用者指定 MariaDB

**理由：**
- 使用者明確要求 MariaDB
- SQLAlchemy ORM 提供抽象層，未來可替換資料庫
- asyncmy 為純 Python async 驅動，與 FastAPI async 生態一致
- 使用 Alembic 管理 schema migration

### 2. 影片來源：yt-dlp Python API

**選擇：** 透過 yt-dlp 的 Python API 直接呼叫（非 subprocess）

**替代方案：**
- subprocess 呼叫 yt-dlp CLI：難以取得進度回呼、錯誤處理不便
- youtube-dl：已不再積極維護

**理由：**
- yt-dlp Python API 支援進度回呼（hook），可追蹤下載百分比
- 使用者的影片在 YouTube 上，yt-dlp 為目前最穩定的下載工具
- 預設下載 mp4 格式、720p 解析度（平衡品質與處理速度）

### 3. 背景任務：FastAPI BackgroundTasks + 狀態輪詢

**選擇：** FastAPI 內建 BackgroundTasks 處理耗時操作，前端輪詢狀態

**替代方案：**
- Celery + Redis：功能完整但架構複雜，MVP 階段過度工程
- WebSocket 即時推送：實作複雜度高

**理由：**
- 單一使用者場景，BackgroundTasks 足夠
- 資料庫記錄任務狀態（pending/processing/completed/failed），前端定時輪詢
- 未來需擴展時可替換為 Celery，介面不變

### 4. 前端架構：React SPA + Video.js + Tailwind CSS

**選擇：** Vite 建置 React TypeScript SPA，Video.js 影片播放，Tailwind CSS 樣式

**替代方案：**
- Next.js SSR：本專案不需 SEO，SPA 即可
- 原生 HTML5 video：缺少自訂控制項與外掛生態

**理由：**
- Video.js 提供成熟的影片播放器 API，支援自訂時間軸標記圖層
- Tailwind CSS 開發速度快，適合功能導向的管理介面
- React Context 管理全域狀態（影片列表、當前標記），初期足夠

### 5. Docker 架構：三服務編排

**選擇：** docker-compose 編排三個服務：app（前端 + 後端）、db（MariaDB）

**服務規劃：**
- `app`：Python 映像，安裝 FFmpeg + yt-dlp + Node.js 建置前端靜態檔，Uvicorn 提供 API 並掛載前端 dist
- `db`：MariaDB 官方映像，資料持久化卷

**替代方案：**
- 前後端分離容器 + Nginx 反向代理：架構更乾淨但配置複雜
- 單一容器：不利於資料庫獨立管理

**理由：**
- 兩個容器簡化部署，減少 Nginx 代理設定
- 開發階段前後端分開跑（Vite dev server + Uvicorn），生產環境合併
- MariaDB 獨立容器方便備份與管理

### 6. 音訊分析策略

**選擇：** 離線分析，librosa 提取特徵 + scipy 訊號處理

**演算法設計：**
- 哨音偵測：帶通濾波（2kHz-4kHz）+ 短時能量峰值偵測
- 歡呼聲偵測：寬頻能量突增 + 持續時間閾值
- 輸出候選時間點列表，使用者確認後轉為正式標記

**理由：**
- 候選時間點作為輔助，降低手動標記工作量
- 參數可調（敏感度、最小間隔），適應不同場館環境
- 不追求完美準確度，著重減少漏標

### 7. 使用者認證與權限控制：JWT + bcrypt

**選擇：** JWT（HS256）身份驗證 + bcrypt 密碼雜湊 + 兩層角色（admin / user）

**替代方案：**
- Session-based 認證：需要伺服器端 session store（如 Redis），架構較複雜
- OAuth2 第三方登入：使用者為特定團隊，不需要第三方登入

**理由：**
- JWT 無狀態，適合單容器部署，無需額外 session store
- python-jose 提供 JWT 簽發/驗證，passlib + bcrypt 處理密碼雜湊
- 兩層角色簡單明瞭：admin 管理帳號與檢視所有資料，user 僅管理自己的資源
- 資源所有權透過 Video 和 Highlight 的 owner_id 追溯，其他資源（Mark、Clip 等）透過 FK 鏈繼承
- 分享連結維持公開存取，不受 JWT 保護
- 初始管理員由 seed script 從環境變數自動建立

### 8. 軌道式標記操作模式

**選擇：** 兩段式錄製標記（按鍵開始 → Esc 結束），生成時間區段色塊

**替代方案：**
- 時間點 + 前後偏移：使用者需理解 offset 概念，不直覺
- 拖曳選取時間區間：需暫停影片，無法邊看邊標

**理由：**
- 貼近專業非線性剪輯軟體（如 DaVinci Resolve）的 Mark In / Mark Out 操作習慣
- 使用者可以邊看邊標記，不需事先估算時間範圍
- 錄製後可拖曳色塊邊緣微調起訖時間
- 分類精簡為 3 類（進攻/防守/失誤），移除「精彩」避免與進攻/防守語意重疊
- 快捷鍵從 4 個改為 3 個（1=進攻 2=防守 3=失誤），降低認知負擔
- 後端 MarkCreate API 同時保留 time+offset 方式（向後相容）與新的 start_time/end_time 直接指定方式

### 9. 檔案儲存結構

```
uploads/
  {video_id}/
    original.mp4          # 原始影片
    audio.wav             # 提取的音訊（分析用）
clips/
  {video_id}/
    {mark_id}.mp4         # 標記對應的片段
highlights/
  {highlight_id}.mp4      # 合併的精華剪輯
```

## Risks / Trade-offs

**[yt-dlp YouTube 限速]** YouTube 可能限制下載頻率或封鎖 IP
→ 加入重試機制（指數退避）、錯誤提示使用者稍後再試、保留直接上傳作為備案

**[FFmpeg 處理效能]** 長時間比賽影片（1-2 小時）處理耗時
→ 使用 `-c copy` 無重編碼切割（毫秒級）；僅合併精華時需重編碼

**[音訊分析準確度]** 籃球場環境噪音複雜，誤報/漏報不可避免
→ 定位為「候選建議」而非「自動標記」，使用者最終確認；提供敏感度調整

**[MariaDB 容器首次啟動]** 需確保資料表在應用啟動前建立
→ Alembic migration 整合至容器啟動腳本；docker-compose depends_on + healthcheck

**[大檔案記憶體]** 音訊分析載入完整音訊可能佔用大量記憶體
→ librosa 支援串流載入（stream=True）；分段處理長音訊

## Future

### 視覺偵測模組（YOLO 籃球/球員偵測）

**研究結論：**
- YOLOv8/v11 COCO 預訓練模型含 `sports ball`（類別 32），可開箱即用偵測籃球
- GitHub 有多個專門專案：AI-Basketball-Shot-Detection-Tracker、AI-Basketball-Referee 等
- 學術模型 BGS-YOLO 達 93.2% mAP，專門針對籃球優化

**推薦路徑：**
1. 先用官方 YOLOv8 COCO 模型做 PoC 驗證
2. 視效果微調或採用 BGS-YOLO
3. 可與現有音訊分析並行，雙通道提高偵測準確度

**啟動時：** 建立新的 OpenSpec change（如 `visual-detection`）
