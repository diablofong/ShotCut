# API Reference

All endpoints are prefixed with `/api`.

!!! tip "Interactive Docs"
    Full interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs` when the server is running.

---

## Authentication

### Login

```http
POST /api/auth/login
```

**Request body:**

```json
{
  "username": "admin",
  "password": "your-password"
}
```

**Response:**

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

A `refresh_token` is also set as an `httpOnly` cookie automatically.

---

### Refresh Token

```http
POST /api/auth/refresh
```

Uses the `httpOnly` cookie to issue a new access token. No request body needed.

---

### Logout

```http
POST /api/auth/logout
```

Revokes the refresh token and clears the cookie.

---

### Current User

```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

---

## Videos

### List Videos

```http
GET /api/videos
Authorization: Bearer <access_token>
```

### Upload Video

```http
POST /api/videos/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file=<video file>
```

### Import from YouTube

```http
POST /api/videos/download
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=..."
}
```

### Download Progress (WebSocket)

```
WS /api/videos/{id}/ws/progress
```

Real-time download progress events:

```json
{
  "status": "downloading",
  "speed": "2.5 MiB/s",
  "eta": "00:32"
}
```

---

## Marks

### List Marks for a Video

```http
GET /api/marks?video_id={id}
Authorization: Bearer <access_token>
```

### Create Mark

```http
POST /api/marks
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "video_id": 1,
  "timestamp": 125.5,
  "category": "offense",
  "players": "7 LeBron, 23 Jordan"
}
```

`category` options: `offense` | `defense` | `turnover`

---

## Clips

### Extract Clips

```http
POST /api/clips
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "mark_ids": [1, 2, 3]
}
```

---

## Highlights

### Generate Highlight Reel

```http
POST /api/highlights/generate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "filter_type": "player",
  "filter_value": "7"
}
```

`filter_type` options: `player` | `category`

---

## Shares

### Create Share Link

```http
POST /api/shares
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "resource_type": "clip",
  "resource_id": 1,
  "expires_in": "7d"
}
```

`expires_in` options: `24h` | `7d` | `30d` | `permanent`

**Response:**

```json
{
  "share_token": "abc123",
  "url": "/share/abc123",
  "expires_at": "2026-03-01T00:00:00Z"
}
```

---

## Health Check

```http
GET /api/health
```

No authentication required. Returns `200 OK` when the service is running.
