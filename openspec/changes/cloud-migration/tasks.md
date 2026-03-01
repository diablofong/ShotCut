# 雲端遷移任務清單

## Phase A~F（已完成）

Phase A（基礎層）、B（後端 API）、C（前端）、D（部署設定）、E（Bug 修復）、F（資安修復）
已全部完成並驗證通過。詳細紀錄見 git log（feature/cloud-migration）。

---

## Phase G0：OpenSpec 文件整理

- [x] G0-1. `proposal.md`：精簡為最終架構摘要
- [x] G0-2. `design.md`：更新為 S3-only 設計
- [x] G0-3. `tasks.md`（本檔）：A~F 摺疊，加入 G/H
- [x] G0-4. `specs/cloud-storage/spec.md`：移除 local，R2 → S3
- [x] G0-5. `specs/config-management/spec.md`：R2\_\* → S3\_\*
- [x] G0-6. `specs/docker-deploy/spec.md`：Preset 層 + bind mount 持久化
- [x] G0-7. `specs/frontend-app/spec.md`：runtime config，移除 VITE_*
- [x] G0-8. `specs/video-ingest/spec.md`：S3-only 路徑

## Phase G：架構重整

- [x] G1. `backend/config.py`：移除 local；R2\_\* → S3\_\*；向後相容 validator
- [x] G2. `backend/services/storage_service.py`：刪 LocalStorageService；R2StorageService → S3StorageService
- [x] G3. `backend/routers/config.py`（新增）：`GET /api/config` 僅回傳 features
- [x] G4. `backend/main.py`：註冊 config router + SIGTERM handler + startup 清理
- [x] G5. `backend/routers/videos.py`：移除所有 local 分支；"r2" → "s3"
- [x] G6. `backend/services/video_service.py`：移除 local 上傳/縮圖路徑
- [x] G7. `backend/services/thumbnail_service.py`：統一走 S3 上傳
- [x] G8. `frontend/src/hooks/useAppConfig.ts`（新增）：runtime 讀 `/api/config`
- [x] G9. `frontend/src/pages/VideosPage.tsx`：移除 VITE_STORAGE_BACKEND；統一 Presigned PUT
- [x] G10. `Dockerfile`：移除 ARG VITE_STORAGE_BACKEND；確認 FFmpeg 已安裝
- [x] G11. 模組層簡化：`docker-compose.yml`、`docker-compose.db.yml`、`docker-compose.s3.yml` 已刪除，改為 3 檔架構
- [x] G12. `docker-compose.selfhosted.yml`：自包含（db + minio + minio-init + app），bind mount `./data/`
- [x] G13. `docker-compose.cloud.yml`：app only，`S3_*` + `R2_*` 向後相容
- [x] G14. `docker-compose.dev.yml`：開發覆寫（port 9001, hot reload）
- [x] G15. `.env` 重整：`S3_*` 統一介面（自建填 MinIO 值，正式填 R2 值），`R2_*` 保留向後相容
- [x] G16. `backend/tests/conftest.py`：新增 mock_storage、r2_video fixture

## Phase H：資安補強

- [x] H1. `backend/services/video_service.py`：confirm 時 filetype 二次驗 + object size 檢查
- [x] H2. `scripts/init-minio.sh`（新增）：mc 建 bucket + private policy（CORS 改由 MinIO 環境變數設定）
- [x] H3. `backend/routers/videos.py`：縮圖 302 presigned GET；confirm_upload rate limit（已於 G5 完成）
- [x] H4. `backend/main.py`：Security Headers middleware（已於 G4 完成）
- [x] H5. `backend/tests/`：補 Phase G/H 新功能測試（test_config_endpoint.py, test_s3_upload.py）

## Phase I：架構安全強化（Opus 審查後補強）

- [x] I1. `backend/routers/auth.py`：Refresh Token Rotation — `/refresh` 每次撤銷舊 token 發新 token
- [x] I2. `docker-compose.selfhosted.yml`：app `depends_on minio-init: service_completed_successfully`
- [x] I3. `backend/services/storage_service.py`：`delete_object`/`upload_file` 改用 `asyncio.to_thread()` 避免阻塞 event loop
- [x] I4. `backend/services/video_service.py`：縮圖生成直接傳 presigned URL 給 FFmpeg，不下載整部影片
- [x] I5. `backend/routers/videos.py`：`confirm_upload` 先設 `status="processing"` 再啟動背景任務（防競態條件）
- [x] I6. `backend/main.py`：`_cleanup_stale_videos` 加入過期 refresh token 清理；`processing` 狀態納入超時重設
- [x] I7. `backend/limiter.py`：優先讀 `CF-Connecting-IP`，其次 `X-Forwarded-For`（⚠️ 見下方討論）
- [x] I8. `scripts/init-minio.sh`：移除有問題的 `mc cors set`；CORS 改由 `docker-compose.selfhosted.yml` 的 `MINIO_API_CORS_ALLOW_ORIGIN` 設定
- [x] I9. `backend/config.py` + `storage_service.py` + `docker-compose.selfhosted.yml`：加入 `S3_PUBLIC_URL`（選填）；建立雙 boto3 client（內部 `minio:9000` / 公開 `localhost:9000`），presigned URL 直接以公開 endpoint 簽章（AWS Sig V4 Host 必須與瀏覽器請求一致，不可事後替換 hostname）
- [x] I10. `backend/routers/videos.py`：新增 `GET /api/videos/{id}/stream-url` 回傳 JSON presigned URL；`<video>` 元素不帶 Authorization header，不可直接用 302 端點
- [x] I11. `frontend/src/services/api.ts` + `frontend/src/pages/VideoDetailPage.tsx`：前端改為先呼叫 `stream-url` 取得 presigned URL（axios 帶 auth），再傳給 video.js，避免 `<video>` 元素 401 問題
- [x] I12. `backend/routers/videos.py`：移除 `video/avi`、`video/x-msvideo` 允許格式（瀏覽器不支援原生播放）；`frontend/src/pages/VideosPage.tsx`：`accept` 屬性限定 mp4/mov/webm/mkv，上傳失敗時顯示後端錯誤訊息
- [x] I13. `backend/requirements.txt`：加入 `websockets==13.1`（uvicorn WebSocket 支援）
- [x] I14. `backend/services/video_service.py`：`_async_process_r2_upload` httpx/FFmpeg 改用 `internal=True` presigned URL（Docker 內部無法存取 localhost:9000）；exception handler 補存 `error_message`

## ⚠️ 待討論：Rate Limiter IP 偵測（I7）

**現況：** 優先信任 `CF-Connecting-IP` > `X-Forwarded-For` > remote address

**疑慮：** 若攻擊者繞過 Cloudflare 直連 server（不走 CF），可自行偽造 `CF-Connecting-IP` 標頭，完全繞過 rate limiting。

**根本解法：** 在防火牆層（Oracle Security List / iptables）只允許 Cloudflare IP 段連入，封鎖直連。

**需討論：**

1. 正式部署時 Oracle VM 是否會設定防火牆只允許 Cloudflare IP？
2. 若不設防火牆，應改為更保守的策略（例如信任固定的 proxy chain 而非 header 值）

## 驗證清單

- [x] G-V1：`pytest --cov` 通過，覆蓋率 >= 50%（45/45 通過，59.18%）
- [x] G-V2：TypeScript build 無 error
- [ ] G-V3：MinIO 完整上傳流程（upload-url → PUT → confirm → 縮圖 → 串流）
- [x] G-V4：`GET /api/config` 不洩漏 S3 credentials（只回傳 features）
- [x] G-V5：前端無 `VITE_*` 依賴
- [x] G-V6：`docker compose -f docker-compose.selfhosted.yml up` 首次啟動自動完成初始化
- [x] G-V7：`docker compose down && up` 資料不丟失（bind mount `./data/`）
- [ ] H-V1：上傳非影片 → confirm 後狀態 failed，S3 物件已刪除（待手動驗證）
- [ ] H-V2：MinIO bucket 拒絕匿名存取（待手動驗證）
- [x] H-V3：縮圖端點回 302，無 token query param（presigned URL 確認）
- [x] H-V4：Security headers 出現在所有 API 回應（X-Content-Type-Options / X-Frame-Options / Referrer-Policy）
- [x] H-V5：SIGTERM 後，進行中下載狀態正確標記 failed（video_id=3 驗證通過）
- [x] I-V1：`/refresh` 使用後舊 token 回傳 401（Rotation 驗證通過）
- [x] I-V2：confirm 同一影片兩次 → 第二次回 400（競態條件驗證通過）
- [x] I-V3：stream / thumbnail 302 redirect 的 Location 使用 `localhost:9000`（非 `minio:9000`），瀏覽器可存取
- [x] I-V4：`GET /api/videos/{id}/stream-url` 回傳 `{"url": "http://localhost:9000/..."}` JSON，前端 video.js 直接播放

## Phase J：縮圖刷新修復（待實作）

**Bug 根本原因：**

- `_async_process_r2_upload` 在縮圖 upload 後（`thumbnail_path` 存 DB）完全沒有發送 WebSocket 廣播
- `status="completed"` 在縮圖生成之前就 commit，前端立刻 fetchVideos → 渲染 thumbnail img → 404（`thumbnail_path` 仍 null）
- 前端 `handleUpload` 等待 `{event: "thumbnail_generated"}` 事件，但後端從未發送此事件

**修復方案：**

- [ ] J1. `backend/services/video_service.py`：`process_r2_upload` 接收 `main_loop`，`_async_process_r2_upload` 縮圖儲存後用 `asyncio.run_coroutine_threadsafe(ws_manager.broadcast(video_id, {event, status}), main_loop)` 廣播
- [ ] J2. `backend/routers/videos.py`：`confirm_upload` 傳遞 `asyncio.get_event_loop()` 給 `process_r2_upload`
- [ ] J3. `frontend/src/pages/VideosPage.tsx`：`handleUpload` WebSocket handler 改監聽 `status === "completed"` 觸發 fetchVideos（而非不存在的 `thumbnail_generated` event）；同時為 `processing` 狀態影片加入 polling 作為 fallback

## 待驗證（手動整合測試）

- G-V3：MinIO 完整上傳流程（upload-url → PUT → confirm → 縮圖 → 串流）— 需修完 Phase J 後驗證
- H-V1：上傳非影片 → confirm 後狀態 failed，S3 物件已刪除
- H-V2：MinIO bucket 拒絕匿名存取（`curl -I http://localhost:9000/shotcut/` → 403）
