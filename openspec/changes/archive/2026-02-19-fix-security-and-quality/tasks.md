## 1. 環境變數安全化（移除硬編碼 fallback）

- [x] 1.1 修改 `backend/auth/security.py`：SECRET_KEY 移除 fallback，未設定時拋出啟動錯誤
- [x] 1.2 修改 `backend/db/database.py`：DATABASE_URL 移除 fallback，未設定時拋出啟動錯誤
- [x] 1.3 修改 `backend/routers/videos.py`：移除 download_video 中的 DATABASE_URL 硬編碼 fallback，改為從 database 模組匯入
- [x] 1.4 修改 `backend/scripts/seed_admin.py`：移除 DATABASE_URL、ADMIN_USERNAME、ADMIN_PASSWORD 的 fallback
- [x] 1.5 更新 `.env.example`：加入 CORS_ORIGINS 與 MAX_UPLOAD_SIZE_MB 說明

## 2. SPA Fallback 路徑遍歷修復

- [x] 2.1 修改 `backend/main.py` 的 `spa_fallback`：用 `os.path.realpath` 驗證路徑在 `frontend_dist` 目錄內，遍歷嘗試返回 index.html

## 3. CORS 設定安全化

- [x] 3.1 修改 `backend/main.py`：從環境變數 CORS_ORIGINS 讀取 origin 清單，移除 `allow_origins=["*"]`

## 4. 精華剪輯 IDOR 修復

- [x] 4.1 在 `backend/auth/dependencies.py` 新增 `verify_highlight_owner()` 輔助函式
- [x] 4.2 修改 `backend/routers/highlights.py` 的 `stream_highlight`：加入擁有者驗證
- [x] 4.3 修改 `backend/routers/highlights.py` 的 `download_highlight`：加入擁有者驗證
- [x] 4.4 修改 `backend/routers/highlights.py` 的 `highlight_thumbnail`：加入擁有者驗證

## 5. 檔案上傳大小限制

- [x] 5.1 修改 `backend/routers/videos.py` 的 `upload_video`：以串流方式讀取並檢查大小限制，超過 MAX_UPLOAD_SIZE_MB 回傳 413
- [x] 5.2 修改 `backend/services/video_service.py` 的 `create_upload`：接受檔案路徑而非 bytes 內容

## 6. Range Header 統一驗證

- [x] 6.1 建立共用函式 `_parse_range_header(range_header, file_size)` 處理邊界驗證，無效 Range 回傳 416
- [x] 6.2 套用至 `backend/routers/videos.py` 的 `stream_video`
- [x] 6.3 套用至 `backend/routers/clips.py` 的片段串流端點
- [x] 6.4 套用至 `backend/routers/highlights.py` 的 `stream_highlight`
- [x] 6.5 套用至 `backend/routers/shares.py` 的 `stream_share`

## 7. 時區與資源洩漏修復

- [x] 7.1 修改 `backend/routers/shares.py`：`datetime.utcnow()` → `datetime.now(timezone.utc)`
- [x] 7.2 修改 `backend/services/video_service.py` 的 `_async_download`：用 try-finally 包裹 engine.dispose()
- [x] 7.3 修改 `backend/services/video_service.py`：移除 yt-dlp 的 `remote_components` 和 `js_runtimes` 設定

## 8. 前端 Polling 修復

- [x] 8.1 修改 `frontend/src/pages/VideosPage.tsx`：修正 useEffect 依賴陣列，避免 polling 無限循環
