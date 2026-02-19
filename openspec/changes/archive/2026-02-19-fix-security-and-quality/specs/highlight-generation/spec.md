## MODIFIED Requirements

### Requirement: 下載精華剪輯
系統 SHALL 提供精華剪輯檔案下載端點。下載端點 MUST 驗證請求者為精華剪輯的擁有者或管理員，非擁有者 SHALL 回傳 403 Forbidden。

#### Scenario: 擁有者下載精華剪輯
- **WHEN** 精華剪輯擁有者請求下載已完成的精華剪輯
- **THEN** 系統回傳該精華剪輯的檔案，Content-Disposition 為 attachment

#### Scenario: 非擁有者嘗試下載精華剪輯
- **WHEN** 非擁有者且非管理員嘗試下載精華剪輯
- **THEN** 系統 SHALL 回傳 403 Forbidden

#### Scenario: 管理員下載任意精華剪輯
- **WHEN** 管理員請求下載任何精華剪輯
- **THEN** 系統允許下載

## ADDED Requirements

### Requirement: 精華剪輯串流權限驗證
系統 SHALL 在精華剪輯的串流端點驗證請求者為擁有者或管理員。

#### Scenario: 擁有者串流精華剪輯
- **WHEN** 精華剪輯擁有者請求串流
- **THEN** 系統回傳影片串流

#### Scenario: 非擁有者嘗試串流精華剪輯
- **WHEN** 非擁有者且非管理員嘗試串流精華剪輯
- **THEN** 系統 SHALL 回傳 403 Forbidden

### Requirement: 精華剪輯縮圖權限驗證
系統 SHALL 在精華剪輯的縮圖端點驗證請求者為擁有者或管理員。

#### Scenario: 擁有者取得精華剪輯縮圖
- **WHEN** 精華剪輯擁有者請求縮圖
- **THEN** 系統回傳縮圖檔案

#### Scenario: 非擁有者嘗試取得精華剪輯縮圖
- **WHEN** 非擁有者且非管理員嘗試取得精華剪輯縮圖
- **THEN** 系統 SHALL 回傳 403 Forbidden
