## MODIFIED Requirements

### Requirement: 建立標記
系統 SHALL 支援在影片上建立時間範圍標記，包含分類標籤與球員編號。建立標記時 MUST 驗證時間值為非負數，且 `start_time` SHALL 小於 `end_time`。`category` MUST 限制為白名單值（offense、defense、turnover、untagged）。`player_numbers` 中的編號 MUST 在 0-999 範圍內。`label` 長度 MUST 不超過 200 字元。`start_offset` 與 `end_offset` MUST 在 0-60 秒範圍內。

#### Scenario: 軌道式錄製標記
- **WHEN** 使用者在播放影片時按下快捷鍵（1=進攻、2=防守、3=失誤）
- **THEN** 影片自動暫停，系統進入錄製模式，記錄起點時間

#### Scenario: 結束錄製標記
- **WHEN** 使用者在錄製模式中按下 Esc
- **THEN** 影片暫停，系統以起點到當前時間建立標記
- **AND** 時間軸上出現對應分類顏色的色塊
- **AND** 顯示 toast 提示「進攻 標記完成 (0:11 ~ 0:38)」

#### Scenario: 取消錄製
- **WHEN** 使用者在錄製模式中點擊「取消」
- **THEN** 系統退出錄製模式，不建立任何標記

#### Scenario: 使用 API 直接指定時間範圍
- **WHEN** 前端傳送 `start_time` 和 `end_time` 至 MarkCreate API
- **THEN** 系統直接以該時間範圍建立標記，不需計算偏移

#### Scenario: 使用 API 時間點加偏移（向後相容）
- **WHEN** 前端傳送 `time` + `start_offset` + `end_offset` 至 MarkCreate API
- **THEN** 系統計算 `start_time = max(0, time - start_offset)` 和 `end_time = time + end_offset`

#### Scenario: 無效的時間範圍
- **WHEN** 前端傳送 `start_time >= end_time` 或負數時間值
- **THEN** 系統 SHALL 回傳 422 驗證錯誤

#### Scenario: 無效的球員編號
- **WHEN** 前端傳送超出 0-999 範圍的 player_number
- **THEN** 系統 SHALL 回傳 422 驗證錯誤

### Requirement: 標記 CRUD
系統 SHALL 提供標記的完整 CRUD（建立、查詢、更新、刪除）操作。查詢標記列表 SHALL 支援 `limit`（預設 100、上限 500）與 `offset`（預設 0）分頁參數。刪除標記 SHALL 回傳 `{"detail": "已刪除"}`。

#### Scenario: 查詢影片的所有標記
- **WHEN** 使用者查詢某部影片的標記列表
- **THEN** 系統回傳該影片的所有標記，依 start_time 排序

#### Scenario: 查詢影片標記（分頁）
- **WHEN** 使用者查詢標記列表並帶入 `limit=20&offset=40`
- **THEN** 系統回傳第 41-60 筆標記

#### Scenario: 更新標記時間範圍
- **WHEN** 使用者修改一個標記的 start_time 或 end_time（透過拖曳色塊邊緣或編輯表單）
- **THEN** 系統更新該標記記錄

#### Scenario: 更新標記分類或球員
- **WHEN** 使用者修改一個標記的分類或球員編號
- **THEN** 系統更新該標記記錄

#### Scenario: 刪除標記
- **WHEN** 使用者刪除一個標記
- **THEN** 系統刪除該標記記錄及其關聯的片段檔案（若已擷取），回傳 `{"detail": "已刪除"}`
