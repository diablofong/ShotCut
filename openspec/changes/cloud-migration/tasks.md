# 雲端遷移任務清單

## Phase A：基礎層

- [x] A1. 新增 `openspec/specs/feature-flags/spec.md` base spec
- [x] A2. 新增 `openspec/specs/cloud-storage/spec.md` base spec
- [x] A3. 修改 `backend/config.py`：新增 Feature Flag、R2 設定欄位
- [x] A4. 新增 `backend/services/storage_service.py`：StorageService 抽象層 + LocalStorageService + R2StorageService
- [x] A5. 新增 `docker-compose.cloud.yml`：MinIO service
- [x] A6. 新增 `.env.cloud.example`

## Phase B：後端 API 修改

- [x] B1. 修改 `backend/models/video.py`：新增 `r2_key` 欄位
- [x] B2. 新增 `alembic/versions/f1a2b3c4d5e6_add_r2_key_to_video.py`（手動撰寫）
- [x] B3. 新增 `GET /api/videos/upload-url` endpoint（`backend/routers/videos.py`）
- [x] B4. 新增 `POST /api/videos/{id}/confirm` endpoint（`backend/routers/videos.py`）
- [x] B5. 修改 `GET /api/videos/{id}/stream`：R2 後端回傳 302 redirect
- [x] B6. 修改 `backend/services/thumbnail_service.py`：R2 模式上傳縮圖
- [x] B7. 修改 `backend/routers/clips.py`：Feature Flag 檢查
- [x] B8. 修改 `backend/routers/highlights.py`：Feature Flag 檢查
- [x] B9. 修改 `backend/routers/shares.py`：Feature Flag 檢查
- [x] B10. 修改 `backend/requirements.txt`：新增 boto3

## Phase C：前端修改

- [x] C1. 修改 `frontend/src/services/api.ts`：新增 getUploadUrl、uploadToR2、confirmUpload
- [x] C2. 修改 `frontend/src/pages/VideosPage.tsx`：Presigned PUT 上傳流程分支

## Phase D：部署設定

- [x] D1. 新增 `.github/workflows/pages.yml`：Cloudflare Pages 自動部署
- [ ] D2. 更新 `README.md` 雲端部署說明（待辦）

## 驗證

- [x] V1. `npx @fission-ai/openspec validate cloud-migration` 通過
- [x] V2. `pytest` 全部通過（SQLite in-memory，23 passed）
- [x] V3. TypeScript 型別檢查通過（Docker build 成功驗證）
- [x] V4. MinIO 本地測試：Presigned PUT 上傳成功（2026-03-01 API 層驗證，見 Bug-01）
- [x] V5. MinIO 本地測試：302 redirect 串流正常（2026-03-01 API 層驗證，見 Bug-01）
- [x] V6. Feature Flag=false：/clips /highlights /shares 回傳 404（2026-03-01 驗證）

## 已知問題（網頁整合測試，2026-03-01）

### Bug-01（高優先）：前端未走 R2 上傳路徑

- **現象**：上傳影片後 MinIO bucket 為空，縮圖 404，WebSocket 無事件
- **根本原因**：`VideosPage.tsx` 以 `import.meta.env.VITE_STORAGE_BACKEND === 'r2'` 判斷路徑。Vite 在 `npm run build` 時將 env 烤入，但 `docker-compose.cloud.yml` 的 `app.build` 沒有傳入 `VITE_STORAGE_BACKEND=r2` build arg，導致前端永遠走本機 multipart 上傳路徑。
- **影響**：V4/V5 僅透過 API 直接測試（curl + docker exec）通過；網頁實際操作未通過
- **修復方向**：在 `Dockerfile` 加入 `ARG VITE_STORAGE_BACKEND`，並在 `docker-compose.cloud.yml` 的 `build.args` 傳入 `VITE_STORAGE_BACKEND: ${STORAGE_BACKEND:-local}`
- **修復任務**：見 E1

### Bug-02（已修復）：路由順序衝突 `/videos/upload-url` vs `/videos/{video_id}`

- **現象**：`GET /api/videos/upload-url` 回傳 422（"upload-url" 被解析為 video_id）
- **狀態**：已修復（2026-03-01），`upload-url` 路由移至 `{video_id}` 前

### Bug-03（已修復）：entrypoint.sh 使用 asyncmy，但只安裝 aiomysql

- **狀態**：已修復（2026-03-01）

## Phase E：Bug 修復

- [ ] E1. `Dockerfile`：加入 `ARG VITE_STORAGE_BACKEND` / `ENV VITE_STORAGE_BACKEND`，並在 `docker-compose.cloud.yml` build args 傳入對應值
- [ ] E2. 重新驗證 V4/V5（網頁上傳流程），確認 MinIO 有檔案、縮圖正確產生
