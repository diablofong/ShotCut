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
- [ ] V4. MinIO 本地測試：Presigned PUT 上傳成功（需基礎設施就緒後測試）
- [ ] V5. MinIO 本地測試：302 redirect 串流正常（需基礎設施就緒後測試）
- [ ] V6. Feature Flag=false：/clips /highlights /shares 回傳 404（待整合測試）
