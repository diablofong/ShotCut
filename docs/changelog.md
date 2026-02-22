# Changelog

## v1.0.0 — 2026-02-22

Initial stable release of ShotCut.

### Features

- **Video Management** — Upload local files or import from YouTube via yt-dlp
- **Real-time Download Progress** — WebSocket-based progress with automatic polling fallback
- **Quick Tagging** — Keyboard shortcuts (1–3) during playback for instant annotation
- **Player Annotation** — Tag player numbers and names per mark
- **Auto Clip Extraction** — FFmpeg-based clip cutting from marks
- **Personal Highlight Reels** — Merge clips by player or category
- **Share Links** — Time-limited share links (24h / 7d / 30d / permanent)
- **Secure Authentication** — JWT Access Token + httpOnly Refresh Token Cookie
- **Role-based Access Control** — Admin and user roles with data isolation
- **Playback Speed Control** — 0.25x to 2x

### Security Fixes

| CVE | Package | Fixed Version |
|-----|---------|--------------|
| CVE-2025-62727 | starlette | 0.49.1 |
| CVE-2025-62611 | aiomysql | 0.3.0 |

Additional security improvements:

- Replaced `python-jose` with `PyJWT` (CVE mitigation)
- Replaced `asyncmy` with `aiomysql` (CVE-2025-62611)
- Upgraded `python-multipart` to 0.0.22 (security fix)
- Upgraded `fastapi` to 0.129.2
- All dependencies pinned to exact secure versions

### CI/CD

- Backend CI: ruff lint + pytest (23/23 tests) + pip-audit + bandit + TruffleHog
- Frontend CI: ESLint + TypeScript type check + npm audit (dev dependencies excluded)
