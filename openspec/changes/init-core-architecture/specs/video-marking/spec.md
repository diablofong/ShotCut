## ADDED Requirements

### Requirement: 建立標記
系統 SHALL 支援在影片的特定時間點建立標記，包含分類標籤與球員編號。

#### Scenario: 建立含分類與球員的標記
- **WHEN** 使用者在影片的某個時間點建立標記，指定分類為「進攻」並關聯球員編號 7
- **THEN** 系統建立標記記錄，包含影片 ID、時間點（秒）、分類標籤、球員編號、時間範圍（前後各 N 秒）

#### Scenario: 從候選時間點快速建立標記
- **WHEN** 使用者選擇一個音訊分析產出的候選時間點並確認建立標記
- **THEN** 系統以該候選時間點建立標記，使用者可補充分類與球員資訊

### Requirement: 標記分類
系統 SHALL 支援以下分類標籤：進攻（offense）、防守（defense）、精彩（highlight）、失誤（turnover）。

#### Scenario: 使用預定義分類
- **WHEN** 使用者建立標記並選擇分類標籤
- **THEN** 系統 SHALL 僅接受 offense、defense、highlight、turnover 四種分類

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
- **THEN** 系統回傳該影片的所有標記，依時間點排序

#### Scenario: 更新標記
- **WHEN** 使用者修改一個標記的分類或球員編號
- **THEN** 系統更新該標記記錄

#### Scenario: 刪除標記
- **WHEN** 使用者刪除一個標記
- **THEN** 系統刪除該標記記錄及其關聯的片段檔案（若已擷取）

### Requirement: 標記時間範圍
每個標記 SHALL 包含一個時間範圍（開始秒數與結束秒數），定義要擷取的片段範圍。

#### Scenario: 設定時間範圍
- **WHEN** 使用者建立標記，指定中心時間點為 45.5 秒，範圍為前 3 秒後 5 秒
- **THEN** 系統記錄開始時間 42.5 秒、結束時間 50.5 秒
