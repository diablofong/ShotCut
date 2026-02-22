# 部署指南

## 環境需求

- [Docker](https://www.docker.com/) 與 Docker Compose

## Docker 部署（推薦）

### 1. 複製專案

```bash
git clone https://github.com/diablofong/ShotCut.git
cd ShotCut
```

### 2. 設定環境變數

```bash
cp .env.example .env
```

開啟 `.env` 並修改以下必要設定：

```env
# 產生強密鑰（最少 32 字符）
SECRET_KEY=<執行：python -c "import secrets; print(secrets.token_urlsafe(32))">

# 資料庫密碼（請使用強密碼）
MYSQL_ROOT_PASSWORD=你的強密碼
MYSQL_PASSWORD=你的強密碼

# 管理員帳號
ADMIN_PASSWORD=你的管理員密碼

# 資料庫連線
DATABASE_URL=mysql+aiomysql://shotcut:<MYSQL_PASSWORD>@db:3306/shotcut
```

### 3. 啟動服務

```bash
docker compose up -d
```

開啟瀏覽器前往 `http://localhost:8000`。

---

## 正式環境部署檢查清單

!!! warning "上線前必須完成"
    以下步驟為安全正式部署的必要設定。

### 環境變數

| 變數 | 要求 |
|------|------|
| `SECRET_KEY` | ≥32 字符，隨機產生 |
| `MYSQL_ROOT_PASSWORD` | ≥16 字符，含大小寫與特殊符號 |
| `MYSQL_PASSWORD` | ≥16 字符，含大小寫與特殊符號 |
| `ADMIN_PASSWORD` | 務必從預設值 `admin1234` 修改 |
| `CORS_ORIGINS` | 僅設定你的正式網域 |

### HTTPS 設定

透過反向代理（nginx 或 Caddy）部署並配置 SSL/TLS：

```nginx
server {
    listen 443 ssl;
    server_name shotcut.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

!!! tip
    設定 `X-Forwarded-Proto: https` 會自動啟用 Cookie Secure Flag，
    **不需要**手動設定 `IS_PRODUCTION=true`。

### CORS 設定

```env
CORS_ORIGINS=https://shotcut.example.com
```

---

## 環境變數參考

| 變數名稱 | 必填 | 預設值 | 說明 |
|---------|------|--------|------|
| `DATABASE_URL` | ✅ | — | MariaDB 連線字串 |
| `SECRET_KEY` | ✅ | — | JWT 簽署密鑰（≥32 字符） |
| `IS_PRODUCTION` | | `false` | 強制啟用 Cookie Secure Flag |
| `ADMIN_USERNAME` | | `admin` | 初始管理員帳號 |
| `ADMIN_PASSWORD` | | `admin1234` | 初始管理員密碼（**務必修改**） |
| `JWT_ACCESS_EXPIRE_MINUTES` | | `15` | Access Token 有效期（分鐘） |
| `JWT_REFRESH_EXPIRE_DAYS` | | `7` | Refresh Token 有效期（天） |
| `CORS_ORIGINS` | | `""` | 允許的 CORS 來源（逗號分隔） |
| `MAX_UPLOAD_SIZE_MB` | | `2048` | 上傳檔案大小上限（MB） |
| `FFMPEG_TIMEOUT` | | `300` | FFmpeg 處理超時（秒） |
| `APP_PORT` | | `8000` | 對外開放的連接埠 |

---

## 常用指令

```bash
# 查看日誌
docker compose logs -f app

# 停止服務
docker compose down

# 更新後重新建置
docker compose build --pull && docker compose up -d

# 執行測試
docker run --rm \
  --entrypoint python \
  -e DATABASE_URL="sqlite+aiosqlite:///:memory:" \
  -e SECRET_KEY="test-secret-key" \
  shotcut-app \
  -m pytest backend/tests/ -v
```
