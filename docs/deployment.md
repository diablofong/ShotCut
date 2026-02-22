# Deployment Guide

## Requirements

- [Docker](https://www.docker.com/) and Docker Compose

## Docker Deployment (Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/diablofong/ShotCut.git
cd ShotCut
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and update the following required values:

```env
# Generate a strong secret key (minimum 32 characters)
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Database credentials (use strong passwords)
MYSQL_ROOT_PASSWORD=your-strong-root-password
MYSQL_PASSWORD=your-strong-db-password

# Admin account
ADMIN_PASSWORD=your-admin-password

# Database connection
DATABASE_URL=mysql+aiomysql://shotcut:<MYSQL_PASSWORD>@db:3306/shotcut
```

### 3. Start Services

```bash
docker compose up -d
```

Open `http://localhost:8000` in your browser.

---

## Production Checklist

!!! warning "Before going live"
    These steps are required for a secure production deployment.

### Environment Variables

| Variable | Requirement |
|----------|-------------|
| `SECRET_KEY` | ≥32 characters, randomly generated |
| `MYSQL_ROOT_PASSWORD` | ≥16 characters, mixed case + symbols |
| `MYSQL_PASSWORD` | ≥16 characters, mixed case + symbols |
| `ADMIN_PASSWORD` | Change from default `admin1234` |
| `CORS_ORIGINS` | Set to your production domain only |

### HTTPS Setup

Deploy behind a reverse proxy (nginx or Caddy) with valid SSL/TLS:

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
    Setting `X-Forwarded-Proto: https` automatically enables the Cookie Secure Flag.
    You do **not** need to set `IS_PRODUCTION=true` manually.

### CORS Configuration

```env
CORS_ORIGINS=https://shotcut.example.com
```

---

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | MariaDB connection string |
| `SECRET_KEY` | ✅ | — | JWT signing key (≥32 chars) |
| `IS_PRODUCTION` | | `false` | Force Cookie Secure Flag |
| `ADMIN_USERNAME` | | `admin` | Initial admin username |
| `ADMIN_PASSWORD` | | `admin1234` | Initial admin password **(change this)** |
| `JWT_ACCESS_EXPIRE_MINUTES` | | `15` | Access token lifetime (minutes) |
| `JWT_REFRESH_EXPIRE_DAYS` | | `7` | Refresh token lifetime (days) |
| `CORS_ORIGINS` | | `""` | Allowed CORS origins (comma-separated) |
| `MAX_UPLOAD_SIZE_MB` | | `2048` | Upload size limit (MB) |
| `FFMPEG_TIMEOUT` | | `300` | FFmpeg processing timeout (seconds) |
| `APP_PORT` | | `8000` | Exposed port |

---

## Useful Commands

```bash
# View logs
docker compose logs -f app

# Stop services
docker compose down

# Rebuild after updates
docker compose build --pull && docker compose up -d

# Run tests
docker run --rm \
  --entrypoint python \
  -e DATABASE_URL="sqlite+aiosqlite:///:memory:" \
  -e SECRET_KEY="test-secret-key" \
  shotcut-app \
  -m pytest backend/tests/ -v
```
