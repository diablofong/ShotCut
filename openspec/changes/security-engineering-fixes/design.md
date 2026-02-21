## Context

ShotCut 專案經過全面安全審查後，發現 15 個關鍵的安全漏洞和工程缺陷。這些問題橫跨前後端、容器部署、CI/CD 管線等多個層面，需要系統性的修復方案。

**當前狀態**：
- 敏感資訊（.env）已簽入 Git 歷史
- Token 儲存在 localStorage（XSS 風險）
- URL 參數傳遞 Token（日誌洩露）
- 容器以 root 用戶運行
- FFmpeg 命令注入風險
- 檔案上傳僅檢查副檔名
- CI/CD 無安全掃描

**約束條件**：
- 必須保持向後相容（除了標註為 BREAKING 的變更）
- 不能影響現有使用者的正常使用（除了需要重新登入）
- 修復必須分階段實施（Critical → High → Medium）
- 遵循 OpenSpec 開發規範

**相關方**：
- 開發團隊：實施修復
- 使用者：需要重新登入（Token 儲存方式改變）
- 維運團隊：更新部署配置

## Goals / Non-Goals

**Goals:**
- 修復所有已識別的 15 個安全漏洞
- 建立自動化安全掃描機制
- 提升專案的生產就緒度
- 最小化對使用者的影響
- 建立安全開發最佳實踐

**Non-Goals:**
- 不重構現有功能邏輯
- 不改變 API 結構（除了認證方式）
- 不升級主要框架版本（FastAPI、React）
- 不重新設計資料庫 schema
- 不實施進階安全功能（如 2FA、審計日誌）- 該階段僅修復基礎安全問題

## Decisions

### Decision 1: Token 儲存方式改為內存 + HttpOnly Cookie

**選擇**：Access Token 存在 React Context（內存），Refresh Token 使用 HttpOnly Cookie

**替代方案**：
- A. 繼續使用 localStorage（被拒絕：XSS 風險）
- B. 所有 Token 都用 HttpOnly Cookie（被拒絕：需後端改動大，且 Cookie 大小限制）
- C. 使用 sessionStorage（被拒絕：仍有 XSS 風險，且頁面關閉即失效）

**理由**：
- Access Token 在內存中，XSS 無法竊取
- Refresh Token 在 HttpOnly Cookie，JavaScript 無法存取
- 重新載入頁面時，可用 Refresh Token 自動取得新 Access Token
- 符合 OWASP 最佳實踐

**實施細節**：
```typescript
// AuthContext.tsx
const [accessToken, setAccessToken] = useState<string | null>(null);

// 登入後
setAccessToken(response.data.access_token);
// Refresh Token 由後端自動設定為 Cookie

// axios interceptor
config.headers.Authorization = `Bearer ${getAccessToken()}`;
```

### Decision 2: 移除 URL Query Parameter Token

**選擇**：所有認證請求改用 Authorization Header 或 Cookie

**替代方案**：
- A. 繼續使用 Query Parameter（被拒絕：日誌洩露風險）
- B. 使用短期一次性 Token（考慮但過於複雜）

**理由**：
- Query Parameter 會被記錄在伺服器日誌、瀏覽器歷史、Referer header
- Authorization Header 是業界標準
- Cookie 自動附加，無需前端手動處理

**實施細節**：
```typescript
// 縮圖：改用 <img> 依賴 Cookie
<img src="/api/videos/1/thumbnail" /> // Cookie 自動附加

// 下載：改用 fetch + Blob
const response = await fetch('/api/clips/1/download', {
  headers: { Authorization: `Bearer ${token}` }
});
const blob = await response.blob();
```

### Decision 3: FFmpeg 路徑驗證與轉義

**選擇**：使用 validate_file_path() + shlex.quote()

**替代方案**：
- A. 白名單允許的字符（被拒絕：過於嚴格，限制合法檔名）
- B. 僅依賴資料庫 ID（部分採用：輸出路徑使用，但輸入需驗證）

**理由**：
- validate_file_path() 使用 realpath 解析符號連結，防止路徑遍歷
- shlex.quote() 正確轉義 shell 特殊字符
- 兩者結合提供深度防護

**實施細節**：
```python
# 驗證所有輸入路徑
validate_file_path(video.file_path, settings.upload_dir)

# Concat 檔案轉義
for clip in clips:
    validate_file_path(clip.file_path, settings.clip_dir)
    f.write(f"file {shlex.quote(clip.file_path)}\n")
```

### Decision 4: 檔案上傳魔數驗證

**選擇**：使用 `filetype` 或 `python-magic` 套件

**替代方案**：
- A. 僅檢查副檔名（被拒絕：當前狀態，不安全）
- B. 使用 ffprobe 完整驗證（被拒絕：效能開銷大，阻塞上傳）
- C. 自行實現魔數檢查（被拒絕：容易出錯，維護成本高）

**理由**：
- `filetype` 套件輕量（無需 libmagic 二進制）
- 讀取前 262 bytes 即可判斷，效能影響小
- 支援所有常見影片格式的魔數

**實施細節**：
```python
import filetype

first_chunk = await file.read(262)
kind = filetype.guess(first_chunk)
if not kind or kind.mime not in ALLOWED_VIDEO_MIMES:
    raise ValueError(f"檔案類型不符: {kind.mime if kind else 'unknown'}")
await file.seek(0)  # 重置以繼續讀取
```

### Decision 5: 容器非 root 用戶

**選擇**：創建 shotcut 用戶，在 Dockerfile 中 USER shotcut

**替代方案**：
- A. 繼續使用 root（被拒絕：安全風險）
- B. 使用 nobody 用戶（考慮但不明確，建議用自定義用戶）

**理由**：
- 符合容器安全最佳實踐
- 降低容器逃逸風險
- 不影響應用程式功能（檔案權限已正確設定）

**實施細節**：
```dockerfile
# Dockerfile
RUN groupadd -r shotcut && useradd -r -g shotcut shotcut \
    && chown -R shotcut:shotcut /app /app/uploads /app/clips ...
USER shotcut
```

### Decision 6: CI/CD 安全掃描工具選擇

**後端**：
- 依賴掃描：`pip-audit`（官方推薦）
- SAST：`bandit`（Python 專用）
- 秘密掃描：TruffleHog（高準確度）

**前端**：
- 依賴掃描：`npm audit`（內建）
- 秘密掃描：TruffleHog

**容器**：
- 映像掃描：Trivy（考慮，但 Phase 2 實施）

**理由**：
- 選擇官方或社群廣泛採用的工具
- 整合至 GitHub Actions 容易
- 免費且開源

### Decision 7: Git 歷史清理方法

**選擇**：使用 BFG Repo-Cleaner（建議）或 git filter-branch

**理由**：
- BFG 比 filter-branch 快 10-720 倍
- 操作更簡單，錯誤風險低
- 保留 HEAD（最新 commit），僅清理歷史

**警告**：
- 會重寫 Git 歷史，所有協作者需重新 clone
- 執行前必須通知團隊

**實施細節**：
```bash
# 使用 BFG
bfg --delete-files .env
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

### Decision 8: 資料庫連接池配置

**選擇**：設定 pool_size=10, max_overflow=20

**理由**：
- FastAPI 預設無連接池配置，可能資源耗盡
- 10 個連接足夠小型應用
- max_overflow 提供彈性應對流量高峰

**實施細節**：
```python
engine = create_async_engine(
    database_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600
)
```

## Risks / Trade-offs

### Risk 1: Token 儲存方式改變導致所有使用者需重新登入

**風險**：使用者體驗影響

**緩解措施**：
- 在部署公告中明確說明
- 前端顯示友善的「系統升級，請重新登入」訊息
- 確保登入流程順暢

### Risk 2: Git 歷史重寫可能影響協作者

**風險**：其他開發者的本地儲存庫衝突

**緩解措施**：
- 提前通知所有協作者
- 提供重新 clone 的指引
- 選擇低活躍時段執行
- 保留舊儲存庫備份

### Risk 3: FFmpeg 路徑驗證可能阻擋合法檔案

**風險**：符號連結或特殊配置的合法檔案被拒絕

**緩解措施**：
- 充分測試各種檔案路徑情境
- 記錄被拒絕的路徑以便調查
- 提供明確的錯誤訊息

### Risk 4: CI/CD 安全掃描可能產生誤報

**風險**：構建因誤報失敗，阻擋開發

**緩解措施**：
- bandit 使用 `# nosec` 註解標註誤報
- TruffleHog 配置忽略測試用假資料
- 建立誤報處理流程（PR 中說明）

### Risk 5: 非 root 容器可能遇到權限問題

**風險**：檔案寫入失敗

**緩解措施**：
- 在 Dockerfile 中正確設定所有目錄的 chown
- 測試所有檔案操作路徑（上傳、切片、精華）
- docker-compose.yml 中 volumes 權限檢查

### Risk 6: 魔數驗證可能誤判某些影片格式

**風險**：特殊編碼的合法影片被拒絕

**緩解措施**：
- 支援主流影片格式魔數（MP4, MOV, AVI, MKV）
- 記錄被拒絕的檔案魔數以便擴充支援
- 提供清晰的錯誤訊息指引使用者

## Migration Plan

### Phase 1: Critical 修復（第 1 週）

**步驟**：
1. **Git 歷史清理**（需團隊協調）
   - 通知所有開發者
   - 使用 BFG 移除 .env
   - 強制推送並要求重新 clone

2. **後端 Token 安全**
   - 修改 `auth.py` 啟用 Cookie Secure Flag
   - 新增 `IS_PRODUCTION` 環境變數支援
   - 移除 Query Parameter Token 支援（後端）

3. **前端 Token 安全**
   - 修改 AuthContext 改用內存儲存
   - 移除所有 localStorage.getItem/setItem('token')
   - 修改所有 URL Token 參數改用 Header

4. **容器安全**
   - 修改 Dockerfile 建立 shotcut 用戶
   - 測試檔案權限

5. **測試與部署**
   - 完整功能測試
   - 通知使用者需重新登入
   - 部署到生產環境

**驗證**：
- `git log --all -- .env` 無結果
- localStorage 不含 token
- 瀏覽器 Cookie 包含 refresh_token（httpOnly）
- `docker exec app whoami` 輸出 shotcut

### Phase 2: High 優先級修復（第 2-3 週）

**步驟**：
1. **FFmpeg 安全**
   - 實施路徑驗證
   - 實施路徑轉義

2. **檔案上傳驗證**
   - 安裝 filetype 套件
   - 實施魔數檢查
   - 實施檔案名清理

3. **部署配置**
   - docker-compose.yml 移除資料庫埠
   - 修改 CORS 設定
   - 新增 .dockerignore

4. **CI/CD 掃描**
   - backend-ci.yml 加入安全掃描步驟
   - frontend-ci.yml 加入安全掃描步驟

**驗證**：
- 上傳偽造副檔名檔案被拒絕
- FFmpeg concat 正確轉義路徑
- CI workflow 包含安全掃描步驟

### Phase 3: Medium 優先級改進（第 4 週）

**步驟**：
1. **依賴更新**
   - `npm audit fix`
   - 更新 minimatch, ajv

2. **配置強化**
   - Secret Key 驗證
   - 資料庫連接池

3. **最終測試**
   - 端到端測試
   - 安全測試

**驗證**：
- `npm audit` 無高嚴重性漏洞
- 系統拒絕弱 Secret Key 啟動

### Rollback Strategy

**如果 Phase 1 失敗**：
- 恢復舊版本代碼
- 使用者可繼續使用（但安全問題仍存在）

**如果 Git 歷史清理出問題**：
- 使用備份儲存庫恢復
- 通知協作者問題

**如果 Token 機制導致無法登入**：
- 緊急 hotfix 恢復 localStorage 支援（臨時）
- 修正問題後再次部署

### Decision 9: Cookie Secure Flag 自動偵測反向代理

**選擇**：登入時檢查 `X-Forwarded-Proto: https` Header，自動決定 Secure Flag

**替代方案**：
- A. 僅依賴 IS_PRODUCTION 手動設定（被改進：使用者容易忘記，nginx 場景下功能不受影響但少了保護）
- B. 預設 secure=True（被拒絕：純 HTTP 環境登入失效）

**理由**：
- 使用反向代理（nginx/Caddy）時，外部連線為 HTTPS，但 app 容器僅看到 HTTP
- nginx 標準行為設定 `X-Forwarded-Proto: https`，可安全用於判斷連線協議
- 使用者無需手動設定 IS_PRODUCTION 即可獲得完整 Secure Flag 保護
- 符合最小化設定原則（零配置即安全）

**實施細節**：
```python
# backend/routers/auth.py
is_secure = settings.is_production or request.headers.get("x-forwarded-proto") == "https"
response.set_cookie(secure=is_secure, ...)
```

## Open Questions

1. **是否需要通知現有使用者系統升級？**
   - 建議：是，透過 email 或系統公告

2. **Git 歷史清理是否需要建立新儲存庫？**
   - 建議：否，使用 BFG 清理即可，但需評估團隊大小

3. **是否需要實施漸進式部署（Canary）？**
   - 建議：如果有多個實例，可先部署到一個實例測試

4. **WebSocket 認證改用 Cookie 是否有跨域問題？**
   - 需測試：確認 CORS 和 Cookie SameSite 設定

5. **是否需要向 GitHub Security Advisory 回報已修復的漏洞？**
   - 建議：否，這些是內部發現的配置問題，非套件漏洞
