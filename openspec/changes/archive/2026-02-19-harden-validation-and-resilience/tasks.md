## 1. Pydantic 欄位驗證強化

- [x] 1.1 修改 `backend/routers/marks.py` 的 `MarkCreate`：`start_time`/`end_time` 加入 `ge=0`；`start_offset`/`end_offset` 加入 `ge=0, le=60`；`category` 改為 `Literal["offense", "defense", "turnover", "untagged"]`；`label` 加入 `max_length=200`；`player_numbers` 元素加入 `ge=0, le=999`；加入 `model_validator` 驗證 `start_time < end_time`
- [x] 1.2 修改 `backend/routers/marks.py` 的 `MarkUpdate`：同上套用驗證，`category` 改為 `Literal` 或 `None`
- [x] 1.3 修改 `backend/routers/marks.py` 的 `PlayerInfo`：`number` 加入 `ge=0, le=999`；`name` 加入 `max_length=100`

## 2. FFmpeg Timeout 與錯誤遮蔽

- [x] 2.1 修改 `backend/services/clip_service.py` 的 `extract_clip`：`subprocess.run` 加入 `timeout=300`，捕捉 `TimeoutExpired`，error_message 改為「影片處理失敗」，stderr 寫入 log
- [x] 2.2 修改 `backend/services/highlight_service.py` 的 `generate_highlight`：同上加入 timeout 與錯誤遮蔽
- [x] 2.3 修改 `backend/services/thumbnail_service.py` 的 `generate_thumbnail`：加入 `timeout=60`

## 3. file_path 二次驗證

- [x] 3.1 在 `backend/utils/streaming.py` 新增 `validate_file_path(file_path, allowed_dir)` 函式：用 `os.path.realpath` 驗證路徑在允許目錄內
- [x] 3.2 修改 `backend/routers/videos.py` 的 `stream_video` 和 `download_video`：加入 file_path 驗證（UPLOAD_DIR）
- [x] 3.3 修改 `backend/routers/clips.py` 的 `stream_clip` 和 `download_clip`：加入 file_path 驗證（CLIP_DIR）
- [x] 3.4 修改 `backend/routers/highlights.py` 的 `stream_highlight` 和 `download_highlight`：加入 file_path 驗證（HIGHLIGHT_DIR）

## 4. 列表端點分頁

- [x] 4.1 修改 `backend/routers/marks.py` 的 `list_marks`：加入 `limit`（預設 100、上限 500）與 `offset`（預設 0）參數
- [x] 4.2 修改 `backend/routers/clips.py` 的 `list_clips`：加入分頁參數
- [x] 4.3 修改 `backend/routers/highlights.py` 的 `list_highlights`：加入分頁參數
- [x] 4.4 修改 `backend/routers/videos.py` 的 `list_videos`：加入分頁參數

## 5. 統一 API 回應格式

- [x] 5.1 修改 `backend/routers/marks.py` 的 `delete_mark`：回傳 `{"detail": "已刪除"}` 取代 `{"ok": True}`
- [x] 5.2 修改 `backend/routers/clips.py` 的 `delete_clip`：回傳 `{"detail": "已刪除"}` 取代 `{"ok": True}`

## 6. 健康檢查端點

- [x] 6.1 修改 `backend/main.py`：加入 `GET /health` 端點，回傳 `{"status": "ok"}`，不需認證

## 7. 前端錯誤處理改善

- [x] 7.1 新增 `frontend/src/components/ErrorBoundary.tsx`：React Error Boundary 元件
- [x] 7.2 修改 `frontend/src/App.tsx`：用 ErrorBoundary 包裹路由
- [x] 7.3 修改 `frontend/src/pages/HighlightsPage.tsx`：catch 區塊顯示錯誤訊息取代靜默忽略
- [x] 7.4 修改 `frontend/src/pages/VideoDetailPage.tsx`：catch 區塊顯示錯誤訊息取代靜默忽略
