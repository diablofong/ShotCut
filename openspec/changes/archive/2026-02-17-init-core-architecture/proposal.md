## Why

ShotCut 是一款針對籃球比賽的影片標記與片段擷取工具，旨在幫助教練與家長快速回顧比賽重點。目前專案僅有空白骨架，尚無任何實際功能。本次變更將建立完整的核心架構，包含影片取得（YouTube 下載 + 直接上傳）、時間點標記與分類、片段擷取、精華剪輯產出、分享連結、前端應用，以及 Docker 容器化部署。透過一次性奠定所有核心能力，確保後續迭代有穩固的基礎。

## What Changes

- 新增 **影片取得模組**：透過 yt-dlp 下載使用者上傳至 YouTube 的比賽影片，同時支援直接檔案上傳作為次要選項
- ~~新增 **音訊分析模組**~~ — 已移除（辨識度不足）
- 新增 **影片標記模組**：提供時間點標記功能，支援分類（進攻/防守/失誤）與球員編號標註
- 新增 **片段擷取模組**：基於標記時間點，使用 FFmpeg 自動切出影片片段
- 新增 **精華剪輯模組**：依球員或標籤自動合併片段，產出個人精華剪輯影片
- 新增 **分享模組**：產生可分享的連結，供教練與家長瀏覽精華剪輯
- 新增 **使用者認證與權限控制**：JWT 身份驗證、bcrypt 密碼雜湊、兩層角色（admin / user）、資源所有權機制
- 新增 **前端應用**：React + TypeScript + Vite + Tailwind CSS + Video.js，包含影片播放器、標記操作介面、管理頁面、登入頁面、使用者管理頁面
- 新增 **Docker 容器化部署**：docker-compose 編排前端、後端、MariaDB、FFmpeg 工作環境
- **BREAKING**：資料庫從 SQLite 改為 MariaDB，使用 SQLAlchemy async + asyncmy 作為 ORM/驅動
- 更新 `requirements.txt`：移除 aiosqlite，新增 sqlalchemy[asyncio]、asyncmy、yt-dlp、alembic

## Capabilities

### New Capabilities

- `video-ingest`：影片取得 -- 透過 yt-dlp 從 YouTube 下載影片，並支援直接檔案上傳。管理影片來源紀錄、下載狀態追蹤、檔案儲存路徑。
- ~~`audio-analysis`~~ — 已移除（辨識度不足）
- `video-marking`：影片標記 -- 提供時間點標記的 CRUD 操作，支援分類標籤（進攻/防守/精彩/失誤）與球員編號關聯。
- `clip-extraction`：片段擷取 -- 基於標記資料，透過 FFmpeg 精確切割原始影片，產出獨立片段檔案並記錄中繼資料。
- `highlight-generation`：精華剪輯產出 -- 依球員編號或標籤篩選片段，自動合併排序為連續的精華剪輯影片。
- `sharing`：分享連結 -- 產生具有唯一識別碼的分享連結，支援存取權限控制，供教練與家長透過瀏覽器觀看精華剪輯。
- `user-auth`：使用者認證與權限控制 -- JWT 身份驗證（HS256）、bcrypt 密碼雜湊、兩層角色（admin / user）、資源所有權機制（owner_id）、管理員帳號種子腳本、前端登入流程與路由保護。
- `frontend-app`：前端應用 -- React SPA，包含影片播放器（Video.js）、標記時間軸操作介面、影片管理列表、精華剪輯瀏覽、分享頁面、登入頁面、使用者管理頁面。
- `docker-deploy`：Docker 容器化部署 -- Dockerfile（前端/後端）、docker-compose.yml 編排所有服務（前端、後端 API、MariaDB、影片處理 worker）。

### Modified Capabilities

<!-- 無既有能力需修改 -- 此為全新專案初始建置 -->

## UX 改善（Phase 2 追加）

### What Changes (追加)

- 新增 **標記內聯編輯**：在影片詳情頁面直接展開編輯標記的時間範圍、分類、標籤、球員編號，無需刪除重建
- 新增 **精華剪輯刪除**：後端 DELETE 端點 + 前端刪除按鈕，含確認對話框與關聯資源清理
- 新增 **統一導航列（Navbar）**：所有頁面使用一致的導航列，包含導航連結與登出按鈕
- 新增 **下載功能**：精華剪輯與片段均可下載至本地
- 新增 **影片重新命名**：支援修改影片標題

## 軌道式標記 UX 重設計（Phase 3 追加）

### What Changes (追加)

- 重設計 **標記操作流程**：從「時間點 + 前後偏移」改為「軌道式範圍標記」（按鍵開始 → 影片暫停 → 播放 → Esc 結束 → 生成時間區段）
- 精簡 **標記分類**：從 4 類（進攻/防守/精彩/失誤）改為 3 類（進攻/防守/失誤），移除語意重疊的「精彩」
- 重設計 **時間軸視覺化**：圓點標記改為彩色區段色塊，支援拖曳邊緣微調起訖時間
- 新增 **錄製模式 UI**：快捷列在錄製中顯示起點/目前時間、Esc 結束/取消按鈕
- 修改 **MarkCreate API**：支援直接傳入 `start_time`/`end_time`（原只支援 `time` + `offset`）
- 修改 **編輯表單**：從 time+offset 改為直接編輯 start_time/end_time

### Modified Capabilities

- `video-marking`：標記操作改為軌道式範圍錄製，分類精簡為 3 類
- `frontend-app`：時間軸改為色塊、快捷列加入錄製模式狀態

## Impact

### 受影響的程式碼
- `backend/`：全部模組皆為新建 -- models、routers、services、db、auth、scripts、main.py
- `frontend/`：全部為新建 -- React 專案初始化、元件、頁面、contexts、服務層
- 專案根目錄：新增 Dockerfile、docker-compose.yml、.env.example、entrypoint.sh

### API
- 新增完整 REST API：影片管理、標記 CRUD、片段擷取、精華剪輯、分享連結

### 相依套件
- **後端新增**：sqlalchemy[asyncio]、asyncmy、yt-dlp、alembic、python-jose[cryptography]、passlib[bcrypt]、bcrypt
- **後端移除**：aiosqlite
- **前端新增**：react、react-dom、typescript、vite、tailwindcss、video.js、axios、react-router-dom
- **系統依賴**：FFmpeg（容器內安裝）、Node.js（yt-dlp JS runtime）、MariaDB（docker-compose 服務）

### 基礎設施
- Docker + docker-compose 為正式部署方式
- MariaDB 持久化資料卷
- 影片檔案儲存於本機掛載卷（uploads/、clips/）
