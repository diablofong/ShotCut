## 1. Phase 1: Critical 安全修復 - Git 歷史清理

- [ ] 1.1 通知所有協作者即將進行 Git 歷史重寫
- [ ] 1.2 建立當前儲存庫完整備份
- [ ] 1.3 安裝 BFG Repo-Cleaner 工具
- [ ] 1.4 執行 `bfg --delete-files .env` 清理歷史
- [ ] 1.5 執行 `git reflog expire --expire=now --all`
- [ ] 1.6 執行 `git gc --prune=now --aggressive`
- [ ] 1.7 驗證 `.env` 不在任何歷史 commit 中（`git log --all --full-history -- .env`）
- [ ] 1.8 強制推送到遠端（`git push --force`）
- [ ] 1.9 通知協作者重新 clone 儲存庫

## 2. Phase 1: Critical 安全修復 - 後端 Token 安全

- [x] 2.1 在 `backend/config.py` 新增 `is_production: bool` 欄位
- [x] 2.2 在 `.env.example` 加入 `IS_PRODUCTION=false` 並註解說明
- [x] 2.3 修改 `backend/routers/auth.py:84` Cookie Secure Flag 改用 `secure=settings.is_production`
- [ ] 2.4 移除 `backend/auth/dependencies.py` 中的 Query Parameter Token 支援（`token_query` 參數）
- [ ] 2.5 修改 `backend/routers/videos.py` WebSocket 端點移除 Query Parameter Token 支援
- [ ] 2.6 修改 `backend/routers/videos.py` 縮圖端點移除 Query Parameter，改用 Cookie 認證
- [ ] 2.7 修改 `backend/routers/clips.py` 下載端點移除 Query Parameter，改支援 Authorization Header
- [ ] 2.8 修改 `backend/routers/highlights.py` 下載端點移除 Query Parameter，改支援 Authorization Header
- [ ] 2.9 測試所有認證端點僅接受 Header 或 Cookie

## 3. Phase 1: Critical 安全修復 - 前端 Token 安全

- [ ] 3.1 修改 `frontend/src/contexts/AuthContext.tsx` 將 Token 從 localStorage 改為 state
- [ ] 3.2 移除所有 `localStorage.getItem('token')` 呼叫
- [ ] 3.3 移除所有 `localStorage.setItem('token', ...)` 呼叫
- [ ] 3.4 修改 `frontend/src/services/api.ts` axios interceptor 從 Context 讀取 Token
- [ ] 3.5 實作頁面重新載入後自動 refresh 取得新 Token
- [ ] 3.6 修改 `frontend/src/pages/VideosPage.tsx` 縮圖 URL 移除 `?token=` 參數
- [ ] 3.7 修改 `frontend/src/pages/VideoDetailPage.tsx` 縮圖 URL 移除 `?token=` 參數
- [ ] 3.8 修改 `frontend/src/pages/ClipsPage.tsx` 下載和縮圖 URL 移除 `?token=` 參數，改用 fetch + Header
- [ ] 3.9 修改 `frontend/src/pages/HighlightsPage.tsx` 下載和縮圖 URL 移除 `?token=` 參數，改用 fetch + Header
- [ ] 3.10 修改 `frontend/src/services/api.ts` WebSocket 連接移除 URL Token，改用 Cookie
- [ ] 3.11 實作下載功能改用 fetch + Blob + URL.createObjectURL
- [ ] 3.12 測試所有認證流程（登入、重新載入、登出）
- [ ] 3.13 驗證 localStorage 不含任何 Token

## 4. Phase 1: Critical 安全修復 - 容器安全

- [ ] 4.1 修改 `Dockerfile` 新增創建 shotcut 用戶的指令
- [ ] 4.2 修改 `Dockerfile` 使用 chown 設定 `/app` 及資料目錄所有權
- [ ] 4.3 修改 `Dockerfile` 在 CMD 前加入 `USER shotcut`
- [ ] 4.4 測試 Docker 映像構建成功
- [ ] 4.5 測試容器啟動後執行 `whoami` 輸出為 shotcut
- [ ] 4.6 測試所有檔案操作（上傳、切片、精華）正常運作

## 5. Phase 1: Critical 安全修復 - 整合測試與部署

- [ ] 5.1 在開發環境執行完整功能測試
- [ ] 5.2 測試使用者登入登出流程
- [ ] 5.3 測試影片上傳和處理
- [ ] 5.4 測試片段和精華生成
- [ ] 5.5 測試管理員功能
- [ ] 5.6 撰寫升級公告（說明需重新登入）
- [ ] 5.7 部署到生產環境
- [ ] 5.8 驗證生產環境 Cookie Secure Flag 啟用
- [ ] 5.9 監控錯誤日誌

## 6. Phase 2: High 優先級 - FFmpeg 安全

- [ ] 6.1 修改 `backend/services/clip_service.py` 在 FFmpeg 調用前驗證 video.file_path
- [ ] 6.2 修改 `backend/services/clip_service.py` 驗證 output_path 在 CLIP_DIR 內
- [ ] 6.3 修改 `backend/services/highlight_service.py` concat 模式中對每個片段路徑執行驗證
- [ ] 6.4 修改 `backend/services/highlight_service.py` 使用 `shlex.quote()` 轉義 concat 檔案中的路徑
- [ ] 6.5 在 highlight_service.py 中 import shlex
- [ ] 6.6 測試 FFmpeg 片段擷取功能
- [ ] 6.7 測試 FFmpeg 精華生成功能
- [ ] 6.8 測試路徑包含特殊字符的情境

## 7. Phase 2: High 優先級 - 檔案上傳驗證

- [ ] 7.1 在 `backend/requirements.txt` 新增 `filetype` 套件
- [ ] 7.2 執行 `pip install -r backend/requirements.txt`
- [ ] 7.3 修改 `backend/services/video_service.py` import filetype
- [ ] 7.4 在 `create_upload_stream` 函數中實作魔數檢查（讀取前 262 bytes）
- [ ] 7.5 定義允許的 MIME 類型清單（video/mp4, video/quicktime, video/x-msvideo, video/x-matroska）
- [ ] 7.6 實作檔案名稱清理函數 `sanitize_filename()`
- [ ] 7.7 在上傳處理中呼叫檔案名稱清理
- [ ] 7.8 測試上傳真實影片檔案成功
- [ ] 7.9 測試上傳偽造副檔名檔案被拒絕
- [ ] 7.10 測試檔案名稱包含路徑遍歷字符被清理

## 8. Phase 2: High 優先級 - 部署配置

- [ ] 8.1 建立 `.dockerignore` 檔案
- [ ] 8.2 在 `.dockerignore` 中加入：.env, .git, .vscode, .idea, *.md, node_modules, __pycache__, data/
- [ ] 8.3 修改 `docker-compose.yml` 移除或註解掉 `ports: - "3306:3306"`
- [ ] 8.4 測試應用容器仍能連接資料庫（透過內部網路）
- [ ] 8.5 測試主機無法連接 `localhost:3306`
- [ ] 8.6 修改 `backend/main.py` CORS 設定明確指定 `allow_methods` 和 `allow_headers`
- [ ] 8.7 將 `allow_methods=["*"]` 改為 `["GET", "POST", "PUT", "DELETE", "PATCH"]`
- [ ] 8.8 將 `allow_headers=["*"]` 改為 `["Content-Type", "Authorization", "X-Request-ID"]`
- [ ] 8.9 測試前端 API 呼叫仍正常運作

## 9. Phase 2: High 優先級 - CI/CD 安全掃描

- [ ] 9.1 修改 `.github/workflows/backend-ci.yml` 在測試後新增安全掃描步驟
- [ ] 9.2 新增步驟：執行 `pip install pip-audit && pip-audit`
- [ ] 9.3 新增步驟：執行 `pip install bandit && bandit -r backend/ -ll`
- [ ] 9.4 新增步驟：使用 TruffleHog Action 執行秘密掃描
- [ ] 9.5 修改 `.github/workflows/frontend-ci.yml` 在測試後新增安全掃描步驟
- [ ] 9.6 新增步驟：執行 `npm audit --audit-level=high`
- [ ] 9.7 新增步驟：使用 TruffleHog Action 執行秘密掃描
- [ ] 9.8 測試觸發 CI workflow 並確認所有掃描步驟執行
- [ ] 9.9 驗證掃描通過或處理發現的問題

## 10. Phase 3: Medium 優先級 - 前端依賴更新

- [ ] 10.1 在 frontend 目錄執行 `npm audit`
- [ ] 10.2 執行 `npm audit fix` 修復可自動修復的漏洞
- [ ] 10.3 檢查 minimatch 版本是否 >= 10.2.1
- [ ] 10.4 檢查 ajv 版本是否 >= 8.18.0
- [ ] 10.5 若未更新，手動更新相關依賴
- [ ] 10.6 執行 `npm install` 安裝更新
- [ ] 10.7 執行 `npm run build` 確認構建成功
- [ ] 10.8 執行前端測試確認無破壞性變更
- [ ] 10.9 再次執行 `npm audit` 驗證無高嚴重性漏洞

## 11. Phase 3: Medium 優先級 - 配置強化

- [ ] 11.1 修改 `backend/config.py` 新增 Secret Key 驗證器
- [ ] 11.2 使用 `@field_validator('secret_key')` 檢查長度 >= 32
- [ ] 11.3 檢查 Secret Key 不為常見預設值（change-me, test, secret）
- [ ] 11.4 修改 `.env.example` SECRET_KEY 加入生成指令註解
- [ ] 11.5 修改 `.env.example` 所有密碼欄位使用強密碼範例
- [ ] 11.6 修改 `backend/db/database.py` 加入連接池配置
- [ ] 11.7 設定 `pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=3600`
- [ ] 11.8 測試系統拒絕弱 Secret Key 啟動
- [ ] 11.9 測試資料庫連接池正常運作

## 12. Phase 3: Medium 優先級 - 最終驗證

- [ ] 12.1 執行完整端到端測試（註冊、登入、上傳、標記、片段、精華、分享）
- [ ] 12.2 執行安全測試：嘗試 XSS 注入
- [ ] 12.3 執行安全測試：嘗試路徑遍歷
- [ ] 12.4 執行安全測試：嘗試 SQL 注入
- [ ] 12.5 執行安全測試：上傳偽造檔案
- [ ] 12.6 檢查瀏覽器 localStorage 無 Token
- [ ] 12.7 檢查瀏覽器 Cookie 有 httpOnly refresh_token
- [ ] 12.8 檢查瀏覽器歷史記錄無 Token 參數
- [ ] 12.9 檢查 `docker exec app whoami` 為 shotcut
- [ ] 12.10 檢查 Git 歷史無 .env（`git log --all --full-history -- .env`）
- [ ] 12.11 驗證 CI 包含所有安全掃描步驟
- [ ] 12.12 更新 README.md 說明安全改進

## 13. 文件更新

- [ ] 13.1 更新 README.md 移除任何過時的安全說明
- [ ] 13.2 在 README.md 加入安全最佳實踐段落
- [ ] 13.3 更新部署說明強調生產環境必須設定 IS_PRODUCTION=true
- [ ] 13.4 更新 .env.example 所有註解說明更清晰
- [ ] 13.5 建立 SECURITY.md 文件說明安全策略（可選）

## 14. 生產環境部署檢查清單

- [ ] 14.1 確認 IS_PRODUCTION=true
- [ ] 14.2 確認 SECRET_KEY 為至少 32 字符隨機字串
- [ ] 14.3 確認所有資料庫密碼已修改為強密碼
- [ ] 14.4 確認 CORS_ORIGINS 僅包含生產域名
- [ ] 14.5 確認使用 HTTPS
- [ ] 14.6 確認資料庫埠未暴露
- [ ] 14.7 確認容器以非 root 用戶運行
- [ ] 14.8 監控應用日誌無異常
- [ ] 14.9 測試所有核心功能
- [ ] 14.10 通知使用者系統已升級
