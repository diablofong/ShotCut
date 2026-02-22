# API 參考

所有端點皆在 `/api` 前綴下。

!!! tip "互動式文件"
    伺服器啟動後，可在 `http://localhost:8000/docs` 查看完整的 Swagger UI 互動式文件。

---

## 認證

### 登入

```http
POST /api/auth/login
```

**請求內容：**

```json
{
  "username": "admin",
  "password": "你的密碼"
}
```

**回應：**

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

同時會自動設定 `refresh_token` 的 `httpOnly` Cookie。

---

### 更新 Token

```http
POST /api/auth/refresh
```

使用 `httpOnly` Cookie 發行新的 Access Token，不需要請求內容。

---

### 登出

```http
POST /api/auth/logout
```

撤銷 Refresh Token 並清除 Cookie。

---

### 當前使用者

```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

---

## 影片

### 影片列表

```http
GET /api/videos
Authorization: Bearer <access_token>
```

### 上傳影片

```http
POST /api/videos/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file=<影片檔案>
```

### 從 YouTube 匯入

```http
POST /api/videos/download
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=..."
}
```

### 下載進度（WebSocket）

```
WS /api/videos/{id}/ws/progress
```

即時下載進度事件：

```json
{
  "status": "downloading",
  "speed": "2.5 MiB/s",
  "eta": "00:32"
}
```

---

## 標記

### 取得影片的標記列表

```http
GET /api/marks?video_id={id}
Authorization: Bearer <access_token>
```

### 建立標記

```http
POST /api/marks
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "video_id": 1,
  "timestamp": 125.5,
  "category": "offense",
  "players": "7 林書豪, 11 王大明"
}
```

`category` 選項：`offense`（進攻）| `defense`（防守）| `turnover`（失誤）

---

## 片段

### 擷取片段

```http
POST /api/clips
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "mark_ids": [1, 2, 3]
}
```

---

## 精華剪輯

### 產生精華剪輯

```http
POST /api/highlights/generate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "filter_type": "player",
  "filter_value": "7"
}
```

`filter_type` 選項：`player`（依球員）| `category`（依分類）

---

## 分享

### 建立分享連結

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

`expires_in` 選項：`24h` | `7d` | `30d` | `permanent`

**回應：**

```json
{
  "share_token": "abc123",
  "url": "/share/abc123",
  "expires_at": "2026-03-01T00:00:00Z"
}
```

---

## 健康檢查

```http
GET /api/health
```

不需要認證。服務正常運作時回傳 `200 OK`。
