## ADDED Requirements

### Requirement: 登入端點速率限制
`POST /api/auth/login` MUST 對每個 IP 限制每分鐘最多 5 次請求。

#### Scenario: 超過登入速率限制
- **WHEN** 同一 IP 在 1 分鐘內發送超過 5 次 POST `/api/auth/login`
- **THEN** 第 6 次及後續請求回傳 429 Too Many Requests，含 `Retry-After` header

#### Scenario: 正常登入不受影響
- **WHEN** 同一 IP 在 1 分鐘內發送 5 次以內的登入請求
- **THEN** 所有請求正常處理，不受速率限制影響

### Requirement: 影片上傳端點速率限制
`POST /api/videos/upload` MUST 對每個認證使用者限制每小時最多 10 次請求。

#### Scenario: 超過上傳速率限制
- **WHEN** 同一使用者在 1 小時內上傳超過 10 次
- **THEN** 第 11 次回傳 429，含 `Retry-After` header

### Requirement: YouTube 下載端點速率限制
`POST /api/videos/download` MUST 對每個認證使用者限制每小時最多 10 次請求。

#### Scenario: 超過下載速率限制
- **WHEN** 同一使用者在 1 小時內發送超過 10 次下載請求
- **THEN** 第 11 次回傳 429，含 `Retry-After` header

### Requirement: 速率限制錯誤格式
速率限制觸發時，回應 SHALL 符合 API 統一錯誤格式。

#### Scenario: 429 回應格式
- **WHEN** 任何速率限制觸發
- **THEN** 回傳 HTTP 429，body 含 `{"detail": "請求過於頻繁，請稍後再試"}` 及 `Retry-After` header
