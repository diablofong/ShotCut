## Design Decisions

### 1. S3StorageService（唯一儲存後端）

移除 `LocalStorageService`，`R2StorageService` 重命名為 `S3StorageService`：

```python
class S3StorageService(StorageService):
    """S3-compatible，支援 MinIO / R2 / AWS S3 / Backblaze B2"""
```

工廠函式 `get_storage_service()` 直接回傳 `S3StorageService`，不再切換。

### 2. 環境變數統一（S3_*）

| 舊變數 | 新變數 |
|--------|--------|
| `R2_ACCESS_KEY_ID` | `S3_ACCESS_KEY_ID` |
| `R2_SECRET_ACCESS_KEY` | `S3_SECRET_ACCESS_KEY` |
| `R2_BUCKET_NAME` | `S3_BUCKET_NAME` |
| `R2_ENDPOINT_URL` | `S3_ENDPOINT_URL` |
| `STORAGE_BACKEND` | （移除） |

`config.py` validator 自動將舊 `R2_*` 映射到 `S3_*`（向後相容）。

### 3. Runtime Config（GET /api/config）

```
GET /api/config → { features: { clips, highlights, sharing } }
```

前端新增 `useAppConfig` hook，app 初始化時讀取，移除 `VITE_STORAGE_BACKEND`。

### 4. 模組化 Docker Compose

```
docker-compose.yml            # app only（核心）
docker-compose.db.yml         # MariaDB 模組（health check + named volume）
docker-compose.s3.yml         # MinIO 模組（不 expose port 9001）
docker-compose.dev.yml        # 開發覆寫（port 9001）
docker-compose.selfhosted.yml # Preset：include db + s3
docker-compose.cloud.yml      # Preset：app only（外部服務）
```

### 5. MinIO 與 S3 變數合併

```yaml
minio:
  environment:
    MINIO_ROOT_USER: ${S3_ACCESS_KEY_ID}
    MINIO_ROOT_PASSWORD: ${S3_SECRET_ACCESS_KEY}
app:
  environment:
    DATABASE_URL: mysql+aiomysql://shotcut:${DB_PASSWORD}@db:3306/shotcut
    S3_ENDPOINT_URL: http://minio:9000
```

使用者只填一套 `S3_*` + `DB_PASSWORD`，selfhosted preset 自動組裝連線字串。

### 6. Presigned URL 安全時效

- PUT（上傳）：**900s**（15 分鐘）
- GET（串流/縮圖）：**1800s**（30 分鐘）

### 7. 測試策略

- **DB**：`sqlite+aiosqlite:///:memory:`（不變）
- **S3**：Mock `S3StorageService` 介面（`mock_storage` fixture）
- **整合測試**：MinIO 手動驗證（不在 CI）
