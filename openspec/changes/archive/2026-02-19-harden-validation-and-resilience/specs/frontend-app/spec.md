## ADDED Requirements

### Requirement: React Error Boundary
前端 SHALL 提供 ErrorBoundary 元件，包裹所有主要路由頁面。當任一元件發生渲染錯誤時 SHALL 顯示友善的錯誤提示頁面，而非白畫面。

#### Scenario: 元件渲染錯誤
- **WHEN** 某頁面元件拋出 JavaScript 錯誤
- **THEN** ErrorBoundary 攔截錯誤，顯示「發生錯誤」提示與重新整理按鈕，不影響其他頁面

## MODIFIED Requirements

### Requirement: 片段與精華剪輯管理
前端 SHALL 提供片段列表瀏覽與精華剪輯產出操作介面。各頁面的資料載入失敗 MUST 顯示錯誤訊息，區分「無資料」與「載入失敗」狀態。

#### Scenario: 瀏覽片段列表
- **WHEN** 使用者進入片段管理頁面
- **THEN** 顯示所有片段卡片，可依球員或標籤篩選

#### Scenario: 點擊片段快速預覽
- **WHEN** 使用者點擊片段卡片或播放按鈕
- **THEN** 頁面自動滾動至預覽區域，影片自動開始播放

#### Scenario: 觸發精華剪輯產出
- **WHEN** 使用者選擇球員或標籤並點擊「產出精華剪輯」
- **THEN** 提交產出請求，顯示處理進度

#### Scenario: 資料載入失敗
- **WHEN** API 請求失敗（網路錯誤、伺服器錯誤）
- **THEN** 頁面 SHALL 顯示錯誤訊息，而非空白列表或靜默忽略
