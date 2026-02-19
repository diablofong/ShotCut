## Why

前一輪安全修復後，專案仍存在輸入驗證不足、錯誤處理缺失、資源控制薄弱等問題。Mark 時間邊界未驗證可能導致無效資料與 FFmpeg 失敗；列表端點無分頁在大量資料時會記憶體爆滿；前端靜默吞錯讓使用者無法判斷載入是否失敗。這些問題在公開專案中會嚴重影響穩定性與使用體驗。

## What Changes

- 強化所有 Pydantic request model 的欄位驗證（時間邊界、類別白名單、球員號碼範圍、URL 長度限制）
- FFmpeg subprocess 加入 timeout 防止無限掛起
- 下載端點二次驗證 file_path 在合法目錄內
- 前端錯誤處理改善：顯示實際錯誤訊息，區分「無資料」與「載入失敗」
- 加入 React Error Boundary 防止單一元件錯誤 crash 整個應用
- 列表端點加入分頁支援（limit/offset）
- FFmpeg 錯誤訊息不直接回傳前端，改為通用訊息
- 加入 /health 端點供 Docker 健康檢查
- 縮圖產生加入 file lock 避免 race condition
- 統一 API 錯誤回應格式

## Capabilities

### New Capabilities

（無）

### Modified Capabilities
- `video-ingest`: 上傳/下載端點 file_path 二次驗證、FFmpeg timeout
- `video-marking`: Mark 時間邊界驗證、Pydantic 欄位強化、列表分頁
- `clip-extraction`: FFmpeg timeout、錯誤訊息遮蔽、列表分頁、file_path 驗證
- `highlight-generation`: FFmpeg timeout、錯誤訊息遮蔽、列表分頁、縮圖 race condition
- `frontend-app`: 錯誤處理改善、Error Boundary
- `docker-deploy`: /health 端點

## Impact

- 後端：所有 routers 與 services 的驗證邏輯強化
- 前端：多個頁面的錯誤處理、新增 ErrorBoundary 元件
- API：列表端點新增 limit/offset 查詢參數（向下相容，預設不分頁）
- Docker：新增 health check 端點
