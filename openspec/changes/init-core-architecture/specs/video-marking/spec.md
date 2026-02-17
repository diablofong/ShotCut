## ADDED Requirements

### Requirement: 建立標記
系統 SHALL 支援在影片上建立時間範圍標記，包含分類標籤與球員編號。

#### Scenario: 軌道式錄製標記
- **WHEN** 使用者在播放影片時按下快捷鍵（1=進攻、2=防守、3=失誤）
- **THEN** 影片自動暫停，系統進入錄製模式，記錄起點時間
- **AND** 快捷列顯示「進攻 標記中 起點 0:11」

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

#### Scenario: 從候選時間點快速建立標記
- **WHEN** 使用者選擇一個音訊分析產出的候選時間點並確認建立標記
- **THEN** 系統以該候選時間點建立標記，使用者可補充分類與球員資訊

### Requirement: 標記分類
系統 SHALL 支援以下分類標籤：進攻（offense）、防守（defense）、失誤（turnover）。

#### Scenario: 使用預定義分類
- **WHEN** 使用者建立標記並選擇分類標籤
- **THEN** 系統 SHALL 僅接受 offense、defense、turnover 三種分類

#### Scenario: 未指定分類
- **WHEN** 使用者建立標記但未指定分類
- **THEN** 系統 SHALL 將分類設為 untagged

### Requirement: 球員編號標記
系統 SHALL 支援在標記上關聯一或多個球員編號。

#### Scenario: 關聯多個球員
- **WHEN** 使用者在一個標記上關聯球員 5 和球員 11
- **THEN** 系統記錄該標記與多個球員編號的關聯

#### Scenario: 未指定球員
- **WHEN** 使用者建立標記但未指定球員編號
- **THEN** 系統建立不含球員關聯的標記

### Requirement: 標記 CRUD
系統 SHALL 提供標記的完整 CRUD（建立、查詢、更新、刪除）操作。

#### Scenario: 查詢影片的所有標記
- **WHEN** 使用者查詢某部影片的標記列表
- **THEN** 系統回傳該影片的所有標記，依 start_time 排序

#### Scenario: 更新標記時間範圍
- **WHEN** 使用者修改一個標記的 start_time 或 end_time（透過拖曳色塊邊緣或編輯表單）
- **THEN** 系統更新該標記記錄

#### Scenario: 更新標記分類或球員
- **WHEN** 使用者修改一個標記的分類或球員編號
- **THEN** 系統更新該標記記錄

#### Scenario: 刪除標記
- **WHEN** 使用者刪除一個標記
- **THEN** 系統刪除該標記記錄及其關聯的片段檔案（若已擷取）

### Requirement: 標記標籤（Label）
每個標記 SHALL 包含一個自訂標籤（label）欄位，用於描述該標記的內容。

#### Scenario: 建立帶標籤的標記
- **WHEN** 使用者建立標記，填寫標籤「三分球」
- **THEN** 系統記錄 label 為「三分球」

#### Scenario: 未填寫標籤
- **WHEN** 使用者建立標記但未填寫標籤
- **THEN** 系統使用分類名稱作為預設標籤（如「進攻」、「防守」）

### Requirement: 時間軸視覺化
時間軸 SHALL 以彩色區段色塊顯示標記，取代圓點標記。

#### Scenario: 色塊顯示
- **WHEN** 影片有標記
- **THEN** 時間軸上顯示對應分類顏色的半透明色塊（進攻=藍、防守=綠、失誤=紅）
- **AND** 色塊寬度對應 start_time 到 end_time 的時間範圍

#### Scenario: 色塊點擊跳轉
- **WHEN** 使用者點擊時間軸上的色塊
- **THEN** 影片跳轉至該標記的 start_time

#### Scenario: 色塊邊緣拖曳微調
- **WHEN** 使用者拖曳色塊的左邊緣或右邊緣
- **THEN** 系統即時更新該標記的 start_time 或 end_time
- **AND** 拖曳過程中顯示時間 tooltip

#### Scenario: 錄製中動態指示
- **WHEN** 系統處於錄製模式
- **THEN** 時間軸上顯示從起點到當前播放位置的半透明色塊，隨播放即時延伸

### Requirement: 標記查詢與篩選
系統 SHALL 支援按分類與球員編號篩選標記列表。

#### Scenario: 按分類篩選標記
- **WHEN** 使用者查詢某影片的「進攻」標記
- **THEN** 系統回傳該影片所有分類為 offense 的標記
