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

## 11. 後端認證基礎設施（user-auth）

- [x] 11.1 新增 backend/auth/security.py（密碼雜湊 bcrypt + JWT 簽發/驗證 HS256）
- [x] 11.2 新增 backend/auth/dependencies.py（get_current_user、require_admin、verify_video_owner 依賴項）
- [x] 11.3 新增 backend/models/user.py（User model：id、username、hashed_password、display_name、role、is_active、created_at）
- [x] 11.4 更新 backend/models/__init__.py 匯出 User model
- [x] 11.5 更新 backend/requirements.txt 加入 python-jose[cryptography]、passlib[bcrypt]、bcrypt
- [x] 11.6 更新 Alembic migration：在初始 migration 中加入 users 表 + videos 和 highlights 新增 owner_id 欄位（nullable FK）

## 12. 後端認證與使用者管理 API

- [x] 12.1 新增 backend/routers/auth.py（POST /api/auth/login 回傳 JWT、GET /api/auth/me 回傳當前使用者）
- [x] 12.2 新增 backend/routers/users.py（管理員專用 CRUD：GET/POST/PUT/DELETE /api/users）
- [x] 12.3 更新 backend/main.py 註冊 auth.router 和 users.router
- [x] 12.4 新增 backend/scripts/seed_admin.py（初始管理員種子腳本，從環境變數讀取帳密）

## 13. 後端所有權欄位與服務修改

- [x] 13.1 修改 backend/models/video.py：新增 owner_id FK 欄位 + owner relationship
- [x] 13.2 修改 backend/models/highlight.py：新增 owner_id FK 欄位 + owner relationship
- [x] 13.3 修改 backend/services/video_service.py：create_download/create_upload 接受 user_id 設定 owner_id、list_videos 支援 owner_id 過濾
- [x] 13.4 修改 backend/services/highlight_service.py：generate_highlight 接受 user_id 設定 owner_id、list 支援 owner_id 過濾

## 14. 後端路由加入認證保護

- [x] 14.1 修改 backend/routers/videos.py：所有端點注入 get_current_user，新增/上傳設 owner_id，列表/詳情/刪除加所有權驗證
- [x] 14.2 修改 backend/routers/analysis.py：所有端點注入 get_current_user，驗證影片所有權
- [x] 14.3 修改 backend/routers/marks.py：所有端點注入 get_current_user，透過 video 鏈驗證所有權
- [x] 14.4 修改 backend/routers/clips.py：所有端點注入 get_current_user，列表過濾 + 刪除所有權驗證
- [x] 14.5 修改 backend/routers/highlights.py：所有端點注入 get_current_user，generate 傳 user_id，列表加 owner_id 過濾
- [x] 14.6 修改 backend/routers/shares.py：POST/DELETE 加 auth 與所有權驗證，GET /shares/{token} 保持公開免登入

## 15. 前端認證基礎設施

- [x] 15.1 新增 frontend/src/contexts/AuthContext.tsx（AuthProvider、useAuth hook、login/logout 邏輯、localStorage token 管理）
- [x] 15.2 修改 frontend/src/services/api.ts：請求攔截器附加 JWT token、回應攔截器處理 401 導向登入、新增 authApi 和 userApi
- [x] 15.3 新增 frontend/src/components/ProtectedRoute.tsx（路由守衛元件，支援 requireAdmin prop）

## 16. 前端頁面

- [x] 16.1 新增 frontend/src/pages/LoginPage.tsx（登入表單、錯誤提示、登入後重導向首頁）
- [x] 16.2 新增 frontend/src/pages/UsersPage.tsx（管理員專屬：使用者列表、新增表單、停用/刪除）
- [x] 16.3 修改 frontend/src/App.tsx：包裹 AuthProvider、登入路由、ProtectedRoute 保護既有路由、SharePage 保持公開、新增 /users 路由
- [x] 16.4 修改所有頁面 header：顯示當前使用者名稱、管理員顯示「使用者管理」連結、登出按鈕

## 17. 部署設定與整合測試

- [x] 17.1 更新 .env.example：新增 ADMIN_USERNAME、ADMIN_PASSWORD、JWT_EXPIRE_MINUTES
- [x] 17.2 更新 entrypoint.sh：alembic upgrade head 後新增 python -m backend.scripts.seed_admin
- [x] 17.3 更新 docker-compose.yml：環境變數傳遞 ADMIN_USERNAME、ADMIN_PASSWORD、JWT_EXPIRE_MINUTES、bind mount 掛載至 ./data/
- [x] 17.4 完整流程測試：登入 API 驗證、JWT 認證、未認證 401、admin 種子建立、前端頁面正常載入

## 18. 修復標記建立前後端對接

- [x] 18.1 Mark model 新增 `label` 欄位（String(200), default=""）
- [x] 18.2 MarkCreate 支援 `time`+`start_offset`+`end_offset`（自動轉 start_time/end_time）、`label` 欄位
- [x] 18.3 MarkOut 回傳 `time`、`label`、`start_offset`、`end_offset`（由 start_time/end_time 反算）
- [x] 18.4 MarkUpdate 同步支援 `label` 更新
- [x] 18.5 產生 Alembic migration 新增 marks.label 欄位

## 19. 修復片段篩選前後端對接

- [x] 19.1 `/clips` 端點新增 `category`、`player_number` 查詢參數
- [x] 19.2 `clip_service.list_clips()` 加入 Mark JOIN 篩選邏輯（按分類、球員編號）
- [x] 19.3 ClipOut 擴充：加入 `category`、`label`、`player_numbers`、`start_time`、`end_time` 欄位（透過 Mark 關聯取得）

## 20. 修復精華剪輯多選前後端對接

- [x] 20.1 Highlight model 新增 `filter_players`（JSON）、`filter_categories`（JSON）欄位，取代舊的 filter_player/filter_category
- [x] 20.2 GenerateRequest 改為 `player_numbers: list[int]`、`categories: list[str]`
- [x] 20.3 `highlight_service.generate_highlight()` 支援多球員+多分類篩選
- [x] 20.4 HighlightOut 回傳 `player_numbers`、`categories`、`created_at`
- [x] 20.5 產生 Alembic migration 新增 highlights.filter_players/filter_categories 欄位

## 21. 鍵盤快捷鍵標記

- [x] 21.1 VideoDetailPage 監聽鍵盤事件（1=進攻、2=防守、3=精彩、4=失誤）
- [x] 21.2 播放中按下數字鍵直接標記當前時間（預設前後各 3 秒），不需暫停
- [x] 21.3 標記後顯示 toast 提示確認標記已建立

## 22. 標記內聯編輯

- [x] 22.1 VideoDetailPage 新增標記展開編輯 UI（點擊卡片展開，可修改 time/offset/category/label/players）
- [x] 22.2 呼叫 `markApi.update()` 儲存修改，成功後刷新列表

## 23. 精華剪輯刪除

- [x] 23.1 後端新增 `DELETE /api/highlights/{highlight_id}`（含權限檢查、刪除檔案/分享/DB 記錄）
- [x] 23.2 `highlight_service.py` 新增 `delete_highlight()` 函式
- [x] 23.3 前端 `highlightApi` 新增 `delete()` 方法
- [x] 23.4 HighlightsPage 每張卡片加刪除按鈕 + 確認對話框

## 24. 統一導航列（Navbar）

- [x] 24.1 建立 `frontend/src/components/Navbar.tsx` 共用導航列元件（Logo + 導航連結 + 使用者名稱 + 登出）
- [x] 24.2 所有頁面（HomePage、VideosPage、VideoDetailPage、ClipsPage、HighlightsPage、UsersPage）移除自行實作的頭部，改用 Navbar

## 25. 精華剪輯下載

- [x] 25.1 後端新增 `GET /api/highlights/{id}/download`（返回檔案附件下載）
- [x] 25.2 HighlightsPage 卡片加下載按鈕

## 26. 片段下載

- [x] 26.1 後端新增 `GET /api/clips/{id}/download`（返回檔案附件下載）
- [x] 26.2 ClipsPage 卡片加下載按鈕

## 27. 影片重新命名

- [x] 27.1 後端新增 `PUT /api/videos/{video_id}`（修改 title）
- [x] 27.2 VideosPage 卡片加重新命名功能

## 28. 軌道式標記 UX 重設計

### 28.1 後端：MarkCreate 支援 start_time/end_time + 分類精簡

- [x] 28.1.1 `marks.py` CATEGORY_LABELS 移除 `highlight`，保留 offense/defense/turnover/untagged
- [x] 28.1.2 `marks.py` valid_categories 移除 `highlight`
- [x] 28.1.3 MarkCreate schema：`time` 改為可選（`float | None = None`），新增 `start_time`/`end_time` 可選欄位，offset 預設改為 8.0/5.0
- [x] 28.1.4 create_mark 函式：支援兩種建立方式（start_time/end_time 優先，fallback 到 time+offset）

### 28.2 前端：時間軸改為軌道式色塊

- [x] 28.2.1 VideoPlayer Mark 介面新增 `start_time`/`end_time` 欄位
- [x] 28.2.2 時間軸渲染從圓點（`.mark-dot`）改為色塊（`.mark-block`），寬度對應時間範圍
- [x] 28.2.3 色塊 hover 效果（不透明度提升）、點擊跳轉至 start_time
- [x] 28.2.4 色塊左右邊緣加 4px 拖曳把手，拖曳時即時更新時間並顯示 tooltip
- [x] 28.2.5 新增 `onMarkUpdate` prop，拖曳結束時呼叫 API 更新 start_time/end_time
- [x] 28.2.6 新增 `recording` prop，錄製中顯示動態延伸的半透明色塊
- [x] 28.2.7 分類顏色與圖例改為 3 個（移除精彩/黃色）

### 28.3 前端：錄製模式 + 快捷列 + 卡片重構

- [x] 28.3.1 CATEGORIES 從 4 個改為 3 個（進攻/防守/失誤），快捷鍵 1/2/3
- [x] 28.3.2 MarkData 介面新增 `start_time`/`end_time`
- [x] 28.3.3 新增 `recording` 狀態（category/label/startTime），按 1-3 進入錄製模式（暫停影片、記錄起點）
- [x] 28.3.4 Esc 鍵結束錄製（暫停影片、呼叫 markApi.create 傳 start_time/end_time、顯示 toast）
- [x] 28.3.5 快捷列 UI 狀態感知：未錄製顯示快捷按鈕、錄製中顯示起點/目前時間 + Esc/取消按鈕
- [x] 28.3.6 快捷列錄製中背景色變為分類淺色
- [x] 28.3.7 編輯表單改用 start_time/end_time 直接編輯（移除 time+offset 欄位）
- [x] 28.3.8 卡片顯示改用 start_time ~ end_time 格式 + 總時長
- [x] 28.3.9 activeMarkId 計算改用 mark.start_time/end_time
- [x] 28.3.10 傳遞 recording 狀態與 onMarkUpdate 回呼給 VideoPlayer

## 29. 球員名字輸入支援

- [x] 29.1 `backend/models/mark.py` MarkPlayer 新增 `player_name` 欄位（String(100), nullable, default=""）
- [x] 29.2 產生 Alembic migration 新增 mark_players.player_name 欄位
- [x] 29.3 `backend/routers/marks.py` 新增 `PlayerInfo` schema（number + name），MarkCreate/MarkUpdate 支援 `players` 欄位
- [x] 29.4 `backend/routers/marks.py` MarkOut 新增 `players: list[PlayerOut]`（向後相容保留 player_numbers）
- [x] 29.5 `backend/routers/marks.py` _mark_to_out 回傳 players 含 number + name
- [x] 29.6 `backend/routers/marks.py` create_mark / update_mark 支援 players 欄位寫入 player_name
- [x] 29.7 前端 MarkData 介面新增 `players: { number: number; name: string }[]`
- [x] 29.8 前端編輯表單改為「球員（號碼 名字，逗號分隔）」格式輸入，解析 "7 林書豪, 11 王大明"
- [x] 29.9 前端卡片顯示改為「7 林書豪, 11 王大明」格式（有名字顯示名字，無名字只顯示號碼）

## 30. 片段管理快速預覽改善

- [x] 30.1 VideoPlayer 元件新增 `autoplay` prop（預設 false，傳入 Video.js 初始化選項）
- [x] 30.2 ClipsPage 點擊片段卡片或播放按鈕後自動滾動至預覽區域
- [x] 30.3 ClipsPage 預覽播放器啟用 autoplay，選擇片段後自動播放

## 31. 修復片段串流時間軸跳轉與精華剪輯刪除

- [x] 31.1 片段串流端點（`/clips/{id}/stream`）加入 HTTP Range 請求支援（與影片串流一致）
- [x] 31.2 修復精華剪輯刪除：`delete_highlight` 使用 `selectinload` 預載關聯，避免 async lazy loading 錯誤
