# ShotCut

**Basketball Game Video Annotation & Highlight Clip Tool**

Upload basketball game footage, quickly annotate and classify key moments, automatically generate highlight clips, and share them with coaches and parents.

---

## Features

| Feature | Description |
|---------|-------------|
| 🎬 Video Management | Upload local files or import via YouTube URL |
| ⚡ Real-time Progress | WebSocket-based YouTube download progress |
| 🏀 Quick Tagging | Press keys 1–3 during playback to tag plays |
| 👤 Player Annotation | Tag player numbers and names |
| ✂️ Auto Clip Extraction | FFmpeg cuts clips automatically from marks |
| 🎞️ Highlight Reels | Merge clips by player or category |
| 🔗 Share Links | Time-limited share links (24h / 7d / 30d / permanent) |
| 🔒 Secure Auth | JWT + Refresh Token, role-based access control |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS + Video.js |
| Backend | Python 3.12 + FastAPI + SQLAlchemy (async) |
| Database | MariaDB 11 |
| Video Processing | FFmpeg + yt-dlp |
| Deployment | Docker + Docker Compose |

## Quick Links

- [Deployment Guide](deployment.md) — Get started with Docker in minutes
- [Usage Guide](usage.md) — How to annotate, clip, and share
- [API Reference](api.md) — Key endpoints for integration
- [Changelog](changelog.md) — What's new in v1.0.0

## Demo

Watch the full walkthrough on [GitHub](https://github.com/diablofong/ShotCut).
