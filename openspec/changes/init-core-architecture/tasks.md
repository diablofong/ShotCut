## 1. Docker 基礎設施與專案骨架

- [x] 1.1 建立 .env.example 範本（MariaDB 密碼、連接埠、資料庫名稱等）
- [x] 1.2 建立後端 Dockerfile（Python 3.11 + FFmpeg + yt-dlp）
- [x] 1.3 建立 docker-compose.yml（app + db 服務、volume 掛載、healthcheck）
- [x] 1.4 建立 docker-compose.dev.yml（開發模式覆蓋：原始碼掛載、熱重載）
- [x] 1.5 更新 backend/requirements.txt（移除 aiosqlite，新增 sqlalchemy、asyncmy、yt-dlp、librosa、scipy、alembic）
- [x] 1.6 建立 backend/main.py FastAPI 應用進入點（含 CORS 中介層）
- [x] 1.7 建立 backend/db/database.py SQLAlchemy async engine 與 session 設定
- [x] 1.8 初始化 Alembic migration 環境與首次 migration 腳本
- [x] 1.9 建立容器啟動腳本（等待 MariaDB ready → 執行 Alembic upgrade → 啟動 Uvicorn）

## 2. 前端專案初始化

- [x] 2.1 在 frontend/ 初始化 Vite + React + TypeScript 專案（package.json、tsconfig.json、vite.config.ts）
- [x] 2.2 安裝並設定 Tailwind CSS
- [x] 2.3 安裝 Video.js、axios、react-router-dom
- [x] 2.4 建立前端目錄結構（pages、components、hooks、services）
- [x] 2.5 建立 API 服務層 frontend/src/services/api.ts（axios instance + 基礎 endpoints）
- [x] 2.6 建立 React Router 路由設定（首頁、影片詳情、片段管理、分享頁面）
- [x] 2.7 更新 Dockerfile 加入前端建置步驟（多階段建置）

## 3. 資料模型

- [x] 3.1 建立 Video model（id、title、source_type、source_url、file_path、status、duration、file_size、created_at）
- [x] 3.2 建立 Candidate model（id、video_id、timestamp、type、confidence、created_at）
- [x] 3.3 建立 Mark model（id、video_id、start_time、end_time、category、created_at）
- [x] 3.4 建立 MarkPlayer 關聯表（mark_id、player_number）
- [x] 3.5 建立 Clip model（id、video_id、mark_id、file_path、duration、file_size、status、created_at）
- [x] 3.6 建立 Highlight model（id、title、filter_player、filter_category、file_path、duration、file_size、status、created_at）
- [x] 3.7 建立 HighlightClip 關聯表（highlight_id、clip_id、order）
- [x] 3.8 建立 ShareLink model（id、highlight_id、token、access_count、created_at）
- [x] 3.9 產生 Alembic migration 並測試 docker-compose up 建表

## 4. 影片取得模組（video-ingest）

- [x] 4.1 建立 backend/services/video_service.py（yt-dlp 下載邏輯、進度回呼、狀態更新）
- [x] 4.2 建立 backend/routers/videos.py（POST /api/videos/download、POST /api/videos/upload）
- [x] 4.3 實作 GET /api/videos 影片列表 API
- [x] 4.4 實作 GET /api/videos/{id} 影片詳情 API
- [x] 4.5 實作 DELETE /api/videos/{id} 刪除影片 API（含檔案清理）
- [x] 4.6 實作 GET /api/videos/{id}/status 下載狀態查詢 API
- [x] 4.7 建立前端影片管理頁面（列表、YouTube URL 輸入、上傳、刪除）
- [x] 4.8 建立前端下載/上傳進度顯示元件

## 5. 音訊分析模組（audio-analysis）

- [x] 5.1 建立 backend/services/audio_service.py（音訊提取、librosa 載入）
- [x] 5.2 實作哨音偵測演算法（帶通濾波 2kHz-4kHz + 峰值偵測）
- [x] 5.3 實作歡呼聲偵測演算法（寬頻能量突增 + 持續時間閾值）
- [x] 5.4 建立 backend/routers/analysis.py（POST /api/videos/{id}/analyze、GET /api/videos/{id}/candidates）
- [x] 5.5 實作分析參數可調功能（敏感度、最小間隔）
- [x] 5.6 建立前端候選時間點側面板元件（列表、確認/忽略按鈕）

## 6. 影片標記模組（video-marking）

- [x] 6.1 建立 backend/routers/marks.py（POST /api/videos/{id}/marks）
- [x] 6.2 實作標記 CRUD API（GET /api/videos/{id}/marks、PUT /api/marks/{id}、DELETE /api/marks/{id}）
- [x] 6.3 實作從候選時間點快速建立標記 API
- [x] 6.4 實作球員編號多對多關聯邏輯
- [x] 6.5 建立前端 Video.js 播放器元件（含自訂控制列）
- [x] 6.6 建立前端時間軸標記圖層（不同分類顏色標示、點擊跳轉）
- [x] 6.7 建立前端快速標記面板（分類選擇、球員編號輸入、時間範圍調整）

## 7. 片段擷取模組（clip-extraction）

- [x] 7.1 建立 backend/services/clip_service.py（FFmpeg -c copy 切割邏輯）
- [x] 7.2 建立 backend/routers/clips.py（POST /api/videos/{id}/clips、GET /api/clips）
- [x] 7.3 實作批次擷取（一次對所有標記產生片段）
- [x] 7.4 實作擷取狀態追蹤與錯誤處理
- [x] 7.5 實作 DELETE /api/clips/{id} 刪除片段 API
- [x] 7.6 建立前端片段列表頁面（篩選、預覽播放、刪除）

## 8. 精華剪輯產出模組（highlight-generation）

- [x] 8.1 建立 backend/services/highlight_service.py（篩選邏輯 + FFmpeg concat 合併）
- [x] 8.2 建立 backend/routers/highlights.py（POST /api/highlights/generate、GET /api/highlights）
- [x] 8.3 實作依球員/標籤/複合條件篩選片段
- [x] 8.4 實作 FFmpeg concat demuxer 合併片段
- [x] 8.5 實作產出狀態追蹤
- [x] 8.6 建立前端精華剪輯產出介面（球員選擇、標籤選擇、產出按鈕、進度）
- [x] 8.7 建立前端精華剪輯列表頁面（播放、下載、分享）

## 9. 分享模組（sharing）

- [x] 9.1 建立 backend/routers/shares.py（POST /api/shares、GET /api/shares/{token}、DELETE /api/shares/{id}）
- [x] 9.2 實作唯一 token 產生與存取計數邏輯
- [x] 9.3 實作公開影片串流端點（透過 token 存取，無需認證）
- [x] 9.4 建立前端分享連結管理介面（建立、複製連結、刪除）
- [x] 9.5 建立前端公開分享播放頁面（訪客觀看）

## 10. 整合測試與收尾

- [ ] 10.1 完整流程測試：YouTube 下載 → 音訊分析 → 標記 → 切片 → 精華剪輯 → 分享（需 Docker 環境）
- [ ] 10.2 驗證 docker-compose up 一鍵啟動正常運作（需 Docker 環境）
- [ ] 10.3 驗證容器重啟後資料持久化（MariaDB volume + 影片檔案 volume）（需 Docker 環境）
- [x] 10.4 確認前端所有頁面路由正常、API 串接完整（TypeScript 檢查通過、Vite 建置成功）
