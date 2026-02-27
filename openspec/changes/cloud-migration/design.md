## Design Decisions

### 1. StorageService 抽象層

採用 Abstract Base Class 模式，定義統一介面：

```python
class StorageService(ABC):
    async def generate_presigned_put_url(key, content_type, expires_in=3600) -> str
    async def generate_presigned_get_url(key, expires_in=3600) -> str
    async def delete_object(key) -> bool
    async def upload_file(local_path, key) -> bool
```

- `LocalStorageService`：local 後端，`generate_presigned_*` 拋出 NotImplementedError
- `R2StorageService`：使用 boto3 S3-compatible API，endpoint 指向 R2

工廠函式 `get_storage_service()` 根據 `settings.storage_backend` 回傳對應實例。

### 2. Presigned PUT 上傳流程

```
前端 → GET /api/videos/upload-url → { upload_url, video_id, key }
前端 → PUT <upload_url> （直接傳至 R2，不經過後端）
前端 → POST /api/videos/{id}/confirm → 觸發縮圖生成
```

Video 記錄在 Step 1 建立（status=pending），Step 3 後更新為 completed。
新增 `r2_key` 欄位記錄 R2 object key（格式：`videos/{year}/{uuid}.mp4`）。

### 3. Feature Flag 系統

在 `backend/config.py` 新增三個 bool 欄位，預設 `True`（向後相容）：

```python
enable_clips: bool = True
enable_highlights: bool = True
enable_sharing: bool = True
```

各 router 在第一個操作前檢查：若為 False，回傳 HTTP 404。

### 4. YouTube 下載相容

yt-dlp 下載至 VM 本地暫存 → `storage_service.upload_file()` 上傳至 R2 → 刪除暫存。
本地模式不變。

### 5. 本地開發環境

新增 `docker-compose.cloud.yml`，包含 MinIO service（模擬 R2）。
`.env.cloud.local` 設定 `R2_ENDPOINT_URL=http://localhost:9000`。
