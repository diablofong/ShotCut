# ShotCut

A basketball game video tagging and clip extraction tool. Upload match footage, quickly tag and classify plays, auto-generate highlight clips, and share them with coaches and parents.

> 中文說明請見 [README.zh-TW.md](README.zh-TW.md)

## Screenshots

> **Demo screenshots coming soon.** To add screenshots, place images in `docs/screenshots/` and update this section.

<!-- Suggested screenshots:
- Video list page with thumbnails and download progress
- Video player with mark timeline
- Highlight generation dialog
- Share link page (public view)
-->

## Features

- **Video Management** — Upload local files or import via YouTube URL (yt-dlp); table UI with search and thumbnail preview
- **Real-time Download Progress** — WebSocket pushes YouTube download progress (speed / ETA); falls back to polling on disconnect
- **Quick Tagging** — Press keys 1–3 during playback to tag Offense / Defense / Turnover; drag timeline blocks to fine-tune timestamps
- **Player Annotation** — Tag player numbers and names (e.g. "7 LeBron, 23 Jordan")
- **Auto Clip Extraction** — FFmpeg cuts clips automatically based on marks
- **Personal Highlight Reels** — Merge clips by player or category into a highlight video
- **Share Links** — Generate share links (24h / 7d / 30d / permanent) for coaches and parents to view without login
- **Playback Speed Control** — 0.25x – 2x speed (slow-motion review / quick scan)
- **Secure Authentication** — JWT Access Token (15 min) + Refresh Token (7 days, httpOnly Cookie); role-based access (admin / user); data isolation

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS + Video.js |
| Backend | Python 3.11 + FastAPI + SQLAlchemy (async) |
| Database | MariaDB 11 |
| Video Processing | FFmpeg |
| Video Download | yt-dlp |
| Real-time | WebSocket (FastAPI native) |
| Security | slowapi rate limiting, bcrypt password hashing |
| Deployment | Docker + Docker Compose |

## Quick Start

### Requirements

- [Docker](https://www.docker.com/) and Docker Compose

### Using Docker (recommended)

```bash
# Copy environment template
cp .env.example .env

# Edit .env — you must change: SECRET_KEY, ADMIN_PASSWORD, database passwords

# Start services
docker compose up -d
```

Open `http://localhost:8000` in your browser.

### Local Development

**Backend:**

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r backend/requirements.txt

cp .env.example .env
# Edit DATABASE_URL to point to your MariaDB instance

alembic upgrade head

uvicorn backend.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server: `http://localhost:5173` — Backend API: `http://localhost:8000`

## Running Tests

Tests use SQLite in-memory — no MariaDB instance required:

```bash
# Run inside Docker (recommended — no local Python needed)
docker run --rm \
  --entrypoint python \
  -e DATABASE_URL="sqlite+aiosqlite:///:memory:" \
  -e SECRET_KEY="test-secret-key" \
  shotcut-app \
  -m pytest backend/tests/ -v --cov=backend
```

**Current status: 23/23 tests passing — 56% coverage** (threshold: 50%)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | MariaDB connection string |
| `SECRET_KEY` | ✅ | — | JWT signing key (random string) |
| `ADMIN_USERNAME` | | `admin` | Initial admin account |
| `ADMIN_PASSWORD` | | `admin1234` | Initial admin password **(change this)** |
| `JWT_ACCESS_EXPIRE_MINUTES` | | `15` | Access token lifetime (minutes) |
| `JWT_REFRESH_EXPIRE_DAYS` | | `7` | Refresh token lifetime (days) |
| `CORS_ORIGINS` | | `""` | Allowed CORS origins (comma-separated) |
| `MAX_UPLOAD_SIZE_MB` | | `2048` | Upload size limit (MB) |
| `FFMPEG_TIMEOUT` | | `300` | FFmpeg processing timeout (seconds) |
| `APP_PORT` | | `8000` | Exposed port |

## Project Structure

```
ShotCut/
├── backend/                # FastAPI backend
│   ├── auth/               # JWT auth & permissions
│   ├── db/                 # Database connection
│   ├── models/             # SQLAlchemy ORM models
│   ├── routers/            # API routes
│   ├── services/           # Business logic
│   ├── tests/              # Integration tests (pytest + httpx)
│   ├── config.py           # Centralized settings (pydantic-settings)
│   ├── limiter.py          # Rate limiting (slowapi)
│   ├── websocket_manager.py# WebSocket connection manager
│   └── main.py             # Application entry point
├── frontend/               # React frontend
│   └── src/
│       ├── components/     # Shared components
│       ├── contexts/       # React contexts (auth, etc.)
│       ├── hooks/          # Custom hooks
│       ├── pages/          # Page components
│       └── services/       # API service layer
├── alembic/                # Database migrations
├── .github/workflows/      # GitHub Actions CI/CD
│   ├── backend-ci.yml      # Backend lint + tests
│   └── frontend-ci.yml     # Frontend lint + type check
├── data/                   # Runtime data (git-ignored)
│   ├── uploads/
│   ├── clips/
│   ├── highlights/
│   ├── thumbnails/
│   └── db/
├── openspec/               # OpenSpec design documents
├── docker-compose.yml      # Production deployment
├── docker-compose.dev.yml  # Development environment
└── Dockerfile
```

## API Endpoints

All endpoints are under the `/api` prefix:

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check (no auth required) |
| `POST /api/auth/login` | Login — returns Access Token + sets Refresh Token cookie |
| `POST /api/auth/refresh` | Exchange Refresh Token for new Access Token |
| `POST /api/auth/logout` | Revoke Refresh Token and clear cookie |
| `GET /api/auth/me` | Current user info |
| `GET /api/videos` | List videos |
| `POST /api/videos/upload` | Upload a video file |
| `POST /api/videos/download` | Import from YouTube URL |
| `WS /api/videos/{id}/ws/progress` | Real-time download progress (WebSocket) |
| `GET /api/marks` | List marks for a video |
| `POST /api/clips` | Extract clips from marks |
| `POST /api/highlights/generate` | Generate highlight reel |
| `POST /api/shares` | Create share link |

Full interactive API docs: `http://localhost:8000/docs` (Swagger UI)

## License

[MIT License](LICENSE)
