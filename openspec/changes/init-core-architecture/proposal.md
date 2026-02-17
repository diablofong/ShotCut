## Why

ShotCut 是一款針對籃球比賽的影片標記與片段擷取工具，旨在幫助教練與家長快速回顧比賽重點。目前專案僅有空白骨架，尚無任何實際功能。本次變更將建立完整的核心架構，包含影片取得（YouTube 下載 + 直接上傳）、音訊分析自動偵測、時間點標記與分類、片段擷取、精華剪輯產出、分享連結、前端應用，以及 Docker 容器化部署。透過一次性奠定所有核心能力，確保後續迭代有穩固的基礎。

## What Changes

- 新增 **影片取得模組**：透過 yt-dlp 下載使用者上傳至 YouTube 的比賽影片，同時支援直接檔案上傳作為次要選項
- 新增 **音訊分析模組**：使用 librosa + scipy 自動偵測哨音與歡呼聲，產生候選時間點
- 新增 **影片標記模組**：提供時間點標記功能，支援分類（進攻/防守/精彩/失誤）與球員編號標註
- 新增 **片段擷取模組**：基於標記時間點，使用 FFmpeg 自動切出影片片段
- 新增 **精華剪輯模組**：依球員或標籤自動合併片段，產出個人精華剪輯影片
- 新增 **分享模組**：產生可分享的連結，供教練與家長瀏覽精華剪輯
- 新增 **使用者認證與權限控制**：JWT 身份驗證、bcrypt 密碼雜湊、兩層角色（admin / user）、資源所有權機制
- 新增 **前端應用**：React + TypeScript + Vite + Tailwind CSS + Video.js，包含影片播放器、標記操作介面、管理頁面、登入頁面、使用者管理頁面
- 新增 **Docker 容器化部署**：docker-compose 編排前端、後端、MariaDB、FFmpeg 工作環境
- **BREAKING**：資料庫從 SQLite 改為 MariaDB，使用 SQLAlchemy async + asyncmy 作為 ORM/驅動
- 更新 `requirements.txt`：移除 aiosqlite，新增 sqlalchemy[asyncio]、asyncmy、yt-dlp、librosa、scipy

## Capabilities

### New Capabilities

- `video-ingest`：影片取得 -- 透過 yt-dlp 從 YouTube 下載影片，並支援直接檔案上傳。管理影片來源紀錄、下載狀態追蹤、檔案儲存路徑。
- `audio-analysis`：音訊分析 -- 使用 librosa 提取音訊特徵，搭配 scipy 進行訊號處理，自動偵測哨音頻段與歡呼聲段落，產出候選時間點列表。
- `video-marking`：影片標記 -- 提供時間點標記的 CRUD 操作，支援分類標籤（進攻/防守/精彩/失誤）與球員編號關聯。
- `clip-extraction`：片段擷取 -- 基於標記資料，透過 FFmpeg 精確切割原始影片，產出獨立片段檔案並記錄中繼資料。
- `highlight-generation`：精華剪輯產出 -- 依球員編號或標籤篩選片段，自動合併排序為連續的精華剪輯影片。
- `sharing`：分享連結 -- 產生具有唯一識別碼的分享連結，支援存取權限控制，供教練與家長透過瀏覽器觀看精華剪輯。
- `user-auth`：使用者認證與權限控制 -- JWT 身份驗證（HS256）、bcrypt 密碼雜湊、兩層角色（admin / user）、資源所有權機制（owner_id）、管理員帳號種子腳本、前端登入流程與路由保護。
- `frontend-app`：前端應用 -- React SPA，包含影片播放器（Video.js）、標記時間軸操作介面、影片管理列表、精華剪輯瀏覽、分享頁面、登入頁面、使用者管理頁面。
- `docker-deploy`：Docker 容器化部署 -- Dockerfile（前端/後端）、docker-compose.yml 編排所有服務（前端、後端 API、MariaDB、影片處理 worker）。

### Modified Capabilities

<!-- 無既有能力需修改 -- 此為全新專案初始建置 -->

## Impact

### 受影響的程式碼
- `backend/`：全部模組皆為新建 -- models、routers、services、db、auth、scripts、main.py
- `frontend/`：全部為新建 -- React 專案初始化、元件、頁面、contexts、服務層
- 專案根目錄：新增 Dockerfile、docker-compose.yml、.env.example、entrypoint.sh

### API
- 新增完整 REST API：影片管理、音訊分析、標記 CRUD、片段擷取、精華剪輯、分享連結

### 相依套件
- **後端新增**：sqlalchemy[asyncio]、asyncmy、yt-dlp、librosa、scipy、alembic、python-jose[cryptography]、passlib[bcrypt]、bcrypt
- **後端移除**：aiosqlite
- **前端新增**：react、react-dom、typescript、vite、tailwindcss、video.js、axios、react-router-dom
- **系統依賴**：FFmpeg（容器內安裝）、Node.js（yt-dlp JS runtime）、MariaDB（docker-compose 服務）

### 基礎設施
- Docker + docker-compose 為正式部署方式
- MariaDB 持久化資料卷
- 影片檔案儲存於本機掛載卷（uploads/、clips/）
