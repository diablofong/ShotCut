## ADDED Requirements

### Requirement: 敏感操作 Rate Limiting
所有敏感操作（修改密碼、刪除使用者、修改使用者權限）SHALL 實施 Rate Limiting，防止濫用和暴力攻擊。

#### Scenario: 修改密碼端點限流
- **WHEN** 使用者嘗試修改密碼
- **THEN** 端點 SHALL 限制為每小時最多 5 次請求

#### Scenario: 刪除使用者端點限流
- **WHEN** 管理員刪除使用者帳號
- **THEN** 端點 SHALL 限制為每分鐘最多 10 次請求

#### Scenario: 批量操作限流
- **WHEN** 執行批量刪除影片等批量操作
- **THEN** 端點 SHALL 限制為每分鐘最多 5 次請求

#### Scenario: 超過限流後的回應
- **WHEN** 請求超過 Rate Limit
- **THEN** 回傳 429 Too Many Requests，包含 Retry-After header 指示何時可重試

### Requirement: 登入端點強化
登入端點的 Rate Limiting SHALL 更嚴格，防止暴力破解密碼攻擊。限流 SHALL 基於 IP 地址和帳號名稱。

#### Scenario: 基於 IP 的登入限流
- **WHEN** 同一 IP 地址嘗試登入
- **THEN** 限制為每分鐘最多 5 次請求

#### Scenario: 基於帳號的登入限流
- **WHEN** 對同一帳號名稱嘗試登入
- **THEN** 限制為每分鐘最多 3 次請求，防止針對特定帳號的暴力破解

#### Scenario: 登入失敗鎖定
- **WHEN** 連續 10 次登入失敗
- **THEN** 該 IP 或帳號 SHALL 被暫時鎖定 15 分鐘

### Requirement: Rate Limiting 監控
系統 SHALL 記錄所有 Rate Limiting 事件，用於安全監控和攻擊偵測。

#### Scenario: 記錄 Rate Limit 事件
- **WHEN** 請求被 Rate Limit 阻擋
- **THEN** 系統 SHALL 記錄：時間戳、IP 地址、端點、使用者（如有）

#### Scenario: 偵測異常流量模式
- **WHEN** 日誌分析發現大量 Rate Limit 事件
- **THEN** 系統 SHALL 標記為潛在攻擊，通知管理員
