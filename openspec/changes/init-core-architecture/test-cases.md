# ShotCut 整合測試案例

> 17 大項、78 個測試案例，涵蓋後端 API + 前端 E2E 全功能驗證

---

## 1. 認證模組

| ID | 案例 | 步驟 | 預期結果 |
|----|------|------|----------|
| 1.1 | 正常登入 | POST `/api/auth/login` body `username=admin&password=xxx` | 200，回傳 `{ access_token, token_type: "bearer" }` |
| 1.2 | 錯誤密碼 | POST `/api/auth/login` body `username=admin&password=wrong` | 401 |
| 1.3 | 無 token 存取 | GET `/api/videos`（不帶 Authorization header） | 401 `認證失敗` |
| 1.4 | 過期/無效 token | GET `/api/videos` header `Authorization: Bearer invalidtoken` | 401 |
| 1.5 | 取得當前使用者 | GET `/api/auth/me` 帶有效 token | 200，回傳 `{ id, username, display_name, role }` |

## 2. 使用者管理

| ID | 案例 | 步驟 | 預期結果 |
|----|------|------|----------|
| 2.1 | Admin 建立使用者 | POST `/api/users` `{ username, password, display_name, role: "user" }` 用 admin token | 200，使用者建立成功 |
| 2.2 | User 無權建立使用者 | POST `/api/users` 用 user token | 403 `需要管理員權限` |
| 2.3 | Admin 列出所有使用者 | GET `/api/users` 用 admin token | 200，回傳全部使用者陣列 |
| 2.4 | Admin 停用使用者 | PUT `/api/users/{id}` `{ is_active: false }` | 200，該使用者無法再登入 |
| 2.5 | Admin 刪除使用者 | DELETE `/api/users/{id}` | 200 |

## 3. 影片管理

| ID | 案例 | 步驟 | 預期結果 |
|----|------|------|----------|
| 3.1 | 上傳影片 | POST `/api/videos/upload` multipart file=test.mp4 | 200，回傳 `{ id, title: "test.mp4", status: "completed" }` |
| 3.2 | YouTube 下載 | POST `/api/videos/download` `{ url: "https://youtu.be/xxx" }` | 200，回傳 `{ id, status: "pending" }`，輪詢 status 直到 completed |
| 3.3 | 影片列表（owner 過濾） | User A 上傳影片 → User B GET `/api/videos` | User B 列表不含 User A 的影片 |
| 3.4 | Admin 看全部 | Admin GET `/api/videos` | 回傳所有使用者的影片 |
| 3.5 | 重新命名 | PUT `/api/videos/{id}` `{ title: "新名稱" }` | 200，title 更新為「新名稱」 |
| 3.6 | 空標題被拒 | PUT `/api/videos/{id}` `{ title: "" }` | 400 `標題不可為空` |
| 3.7 | 刪除影片 | DELETE `/api/videos/{id}` | 200，檔案從磁碟移除 |
| 3.8 | 串流（完整） | GET `/api/videos/{id}/stream`（無 Range header） | 200，`Accept-Ranges: bytes`，完整影片內容 |
| 3.9 | 串流（Range） | GET `/api/videos/{id}/stream` header `Range: bytes=0-1023` | 206，`Content-Range: bytes 0-1023/{total}`，回傳 1024 bytes |
| 3.10 | 串流（中段 Range） | GET `/api/videos/{id}/stream` header `Range: bytes=50000-51023` | 206，回傳正確位元組範圍 |

## 4. 音訊分析

| ID | 案例 | 步驟 | 預期結果 |
|----|------|------|----------|
| 4.1 | 觸發分析 | POST `/api/videos/{id}/analyze` | 200，背景開始分析 |
| 4.2 | 取得候選時間點 | GET `/api/videos/{id}/candidates`（分析完成後） | 200，回傳 `[{ id, time, type, confidence }]` |
| 4.3 | 無影片檔案 | POST `/api/videos/999/analyze` | 404 |

## 5. 標記 CRUD（軌道式）

| ID | 案例 | 步驟 | 預期結果 |
|----|------|------|----------|
| 5.1 | 建立（start_time/end_time） | POST `/api/videos/{id}/marks` `{ start_time: 11.0, end_time: 38.0, category: "offense", label: "進攻" }` | 200，回傳 `{ id, start_time: 11.0, end_time: 38.0, category: "offense" }` |
| 5.2 | 建立（time+offset 向後相容） | POST `{ time: 20.0, start_offset: 8.0, end_offset: 5.0, category: "defense" }` | 200，`start_time=12.0, end_time=25.0` |
| 5.3 | 建立（未提供時間） | POST `{ category: "offense" }`（無 time 也無 start_time） | 400 `需提供 start_time/end_time 或 time` |
| 5.4 | 建立（offset 邊界） | POST `{ time: 3.0, start_offset: 8.0 }` | `start_time=0`（不能為負） |
| 5.5 | 列表排序 | GET `/api/videos/{id}/marks`（建立多個標記後） | 按 start_time 升冪排序 |
| 5.6 | 更新起訖時間 | PUT `/api/marks/{id}` `{ start_time: 10.0, end_time: 35.0 }` | 200，時間更新 |
| 5.7 | 更新分類 | PUT `/api/marks/{id}` `{ category: "turnover" }` | 200，分類改為 turnover |
| 5.8 | 更新球員（含名字） | PUT `/api/marks/{id}` `{ players: [{ number: 7, name: "林書豪" }, { number: 11, name: "王大明" }] }` | 200，players 含 number + name |
| 5.8b | 更新球員（僅編號，向後相容） | PUT `/api/marks/{id}` `{ player_numbers: [7, 11] }` | 200，player_numbers 為 [7, 11]，players name 為空 |
| 5.9 | 刪除標記 | DELETE `/api/marks/{id}` | 200 |
| 5.10 | 他人標記不可存取 | User B PUT `/api/marks/{userA_mark_id}` | 403 `無權存取此影片` |

## 6. 標記分類驗證

| ID | 案例 | 步驟 | 預期結果 |
|----|------|------|----------|
| 6.1 | offense 有效 | POST marks `{ ..., category: "offense" }` | 200 |
| 6.2 | defense 有效 | POST marks `{ ..., category: "defense" }` | 200 |
| 6.3 | turnover 有效 | POST marks `{ ..., category: "turnover" }` | 200 |
| 6.4 | highlight 被拒 | POST marks `{ ..., category: "highlight" }` | 400 `分類必須為:` |
| 6.5 | 未指定分類 | POST marks `{ start_time: 0, end_time: 10 }`（不帶 category） | 200，category 預設為 "untagged" |
| 6.6 | 未填標籤自動帶入 | POST marks `{ ..., category: "offense" }`（不帶 label） | label 自動為「進攻」 |

## 7. 片段擷取

| ID | 案例 | 步驟 | 預期結果 |
|----|------|------|----------|
| 7.1 | 批次擷取 | 建立 3 個標記 → POST `/api/videos/{id}/clips` | 200，產生 3 個片段，每個對應一個標記 |
| 7.2 | 片段列表 | GET `/api/clips` | 回傳所有片段，含 category/label/player_numbers/start_time/end_time |
| 7.3 | 按分類篩選 | GET `/api/clips?category=offense` | 只回傳 offense 片段 |
| 7.4 | 按球員篩選 | GET `/api/clips?player_number=7` | 只回傳含球員 7 的片段 |
| 7.5 | 下載片段 | GET `/api/clips/{id}/download` | 200，Content-Disposition 附件下載 |
| 7.6 | 刪除片段 | DELETE `/api/clips/{id}` | 200，檔案從磁碟移除 |

## 8. 精華剪輯

| ID | 案例 | 步驟 | 預期結果 |
|----|------|------|----------|
| 8.1 | 產出（多球員+多分類） | POST `/api/highlights/generate` `{ player_numbers: [7,11], categories: ["offense","defense"] }` | 200，建立精華剪輯記錄，FFmpeg 合併片段 |
| 8.2 | 產出（無符合片段） | POST generate `{ player_numbers: [99] }` | 400 或空結果提示 |
| 8.3 | 精華列表 | GET `/api/highlights` | 回傳當前使用者的精華剪輯 |
| 8.4 | 下載精華 | GET `/api/highlights/{id}/download` | 200，附件下載 |
| 8.5 | 刪除精華 | DELETE `/api/highlights/{id}` | 200，檔案 + 分享連結 + DB 記錄全清 |

## 9. 分享

| ID | 案例 | 步驟 | 預期結果 |
|----|------|------|----------|
| 9.1 | 建立分享連結 | POST `/api/shares` `{ highlight_id: 1 }` | 200，回傳 `{ id, token, url }` |
| 9.2 | 公開存取 | GET `/api/shares/{token}`（無 Authorization） | 200，回傳精華剪輯資訊 + 串流 URL |
| 9.3 | 無效 token | GET `/api/shares/invalidtoken` | 404 |
| 9.4 | 刪除分享 | DELETE `/api/shares/{id}` | 200 |

---

## 10. 前端：登入流程

| ID | 案例 | 操作 | 預期結果 |
|----|------|------|----------|
| 10.1 | 正常登入 | 輸入帳密 → 點「登入」 | 導向首頁，Navbar 顯示使用者名稱 |
| 10.2 | 錯誤密碼 | 輸入錯誤密碼 → 點「登入」 | 顯示紅色錯誤提示，停留在登入頁 |
| 10.3 | 登出 | 點 Navbar「登出」 | 導向登入頁，token 從 localStorage 移除 |
| 10.4 | 未登入重導 | 直接訪問 `/videos` | 自動導向 `/login` |

## 11. 前端：影片上傳與播放

| ID | 案例 | 操作 | 預期結果 |
|----|------|------|----------|
| 11.1 | 上傳影片 | 影片頁面 → 選擇 mp4 → 上傳 | 列表出現新影片，狀態為 completed |
| 11.2 | 進入影片詳情 | 點擊影片卡片 | 進入詳情頁，Video.js 播放器載入，影片可播放 |
| 11.3 | 時間軸點擊 | 點擊時間軸中間位置 | 影片跳轉到對應時間，playhead 移動 |
| 11.4 | 時間軸 hover | 滑鼠在時間軸上移動 | 顯示時間 tooltip（如 1:23） |

## 12. 前端：軌道式標記（核心流程）

| ID | 案例 | 操作 | 預期結果 |
|----|------|------|----------|
| 12.1 | 開始錄製 | 影片播放中按鍵盤 `1` | 影片暫停，快捷列變為錄製模式（淺藍背景），顯示「進攻 標記中 起點 0:XX」，脈衝動畫 |
| 12.2 | 錄製中播放 | 錄製模式下點影片播放按鈕 | 影片繼續播放，快捷列「目前」時間持續更新 |
| 12.3 | 結束錄製 | 錄製中按 `Esc` | 影片暫停，Toast 顯示「進攻 標記完成 (0:11 ~ 0:38)」藍色背景，時間軸出現藍色色塊 |
| 12.4 | 取消錄製 | 錄製中點「取消」按鈕 | 退出錄製模式，不建立標記，快捷列恢復預設 |
| 12.5 | 防守標記 | 按 `2` → 播放 → `Esc` | 綠色色塊出現，Toast 顯示「防守 標記完成」綠色背景 |
| 12.6 | 失誤標記 | 按 `3` → 播放 → `Esc` | 紅色色塊出現，Toast 顯示「失誤 標記完成」紅色背景 |
| 12.7 | 重複按鍵忽略 | 錄製中再按 `2` | 無反應（已在錄製中，忽略新的開始請求） |
| 12.8 | 太短標記 | 按 `1` → 立即 `Esc`（<0.5秒） | Toast 顯示「標記時間太短」，不建立標記 |
| 12.9 | 點擊按鈕開始 | 點快捷列「1 進攻」按鈕 | 與按鍵盤 `1` 相同效果 |
| 12.10 | 輸入框中不觸發 | 焦點在編輯表單 input → 按 `1` | 不觸發錄製（只輸入字元） |

## 13. 前端：色塊互動

| ID | 案例 | 操作 | 預期結果 |
|----|------|------|----------|
| 13.1 | 色塊顯示 | 建立標記後觀察時間軸 | 出現對應類別顏色的半透明色塊，寬度對應時間範圍 |
| 13.2 | 色塊 hover | 滑鼠移到色塊上 | 色塊變為較不透明（高亮） |
| 13.3 | 色塊點擊 | 點擊色塊 | 影片跳轉到該標記的 start_time |
| 13.4 | 拖曳左端 | 拖曳色塊左邊緣向右 | 色塊起點移動，顯示時間 tooltip，放開後 API 更新 start_time |
| 13.5 | 拖曳右端 | 拖曳色塊右邊緣向左 | 色塊終點移動，放開後 API 更新 end_time |
| 13.6 | 最小寬度 | 拖曳到幾乎重疊 | 色塊保持最小 0.5 秒差距 |
| 13.7 | 錄製中色塊 | 進入錄製模式後播放影片 | 時間軸上出現虛線邊框的半透明色塊，隨播放向右延伸 |

## 14. 前端：標記編輯

| ID | 案例 | 操作 | 預期結果 |
|----|------|------|----------|
| 14.1 | 展開編輯 | 點右側標記卡片「編輯」 | 卡片展開編輯表單：分類按鈕、標籤、起點、終點、球員 |
| 14.2 | 修改分類 | 點「防守」按鈕 → 儲存 | 色塊顏色從藍變綠，卡片更新 |
| 14.3 | 修改起訖時間 | 修改起點為 5.0、終點為 30.0 → 儲存 | 卡片顯示 0:05 ~ 0:30，色塊位置更新 |
| 14.4 | 指定球員（含名字） | 輸入「7 林書豪, 11 王大明」→ 儲存 | 卡片顯示「7 林書豪, 11 王大明」 |
| 14.4b | 指定球員（僅編號） | 輸入「7, 11」→ 儲存 | 卡片顯示「7 號, 11 號」 |
| 14.5 | 收合編輯 | 點「收合」 | 編輯表單收起，卡片恢復摘要模式 |
| 14.6 | 刪除標記 | 點編輯表單「刪除」 | 標記從列表移除，時間軸色塊消失 |

## 15. 前端：片段擷取

| ID | 案例 | 操作 | 預期結果 |
|----|------|------|----------|
| 15.1 | 批次擷取 | 建立多個標記 → 點「批次擷取片段」 | 提示「片段擷取已開始」，片段管理頁面出現對應片段 |
| 15.2 | 無標記時禁用 | 無標記時觀察「批次擷取片段」按鈕 | 按鈕灰色禁用 |
| 15.3 | 片段列表 | 進入片段管理頁面 | 顯示所有擷取的片段，含分類、時間範圍 |
| 15.4 | 點擊片段自動播放 | 點擊片段卡片 | 頁面滾動至預覽區域，影片自動開始播放 |
| 15.5 | 切換片段預覽 | 正在預覽片段 A → 點擊片段 B | 預覽切換為片段 B 並自動播放 |
| 15.6 | 播放按鈕 | 點擊片段操作列的「播放」按鈕 | 與點擊卡片相同效果，自動滾動並播放 |

## 16. 前端：精華剪輯

| ID | 案例 | 操作 | 預期結果 |
|----|------|------|----------|
| 16.1 | 產出精華 | 精華頁面 → 勾選球員+分類 → 產出 | 精華剪輯出現在列表 |
| 16.2 | 下載精華 | 點精華卡片「下載」 | 瀏覽器開始下載 mp4 檔案 |
| 16.3 | 分享精華 | 點「分享」→ 複製連結 | 產生分享 URL，可在新分頁開啟播放 |
| 16.4 | 刪除精華 | 點「刪除」→ 確認 | 精華從列表移除 |

## 17. 前端：權限隔離

| ID | 案例 | 操作 | 預期結果 |
|----|------|------|----------|
| 17.1 | User 看不到他人影片 | User A 上傳影片 → 登入 User B → 影片頁面 | User B 列表中無 User A 的影片 |
| 17.2 | User 不可存取他人影片 | User B 直接訪問 `/videos/{userA_video_id}` | 403 或 404 |
| 17.3 | Admin 可見全部 | Admin 登入 → 影片頁面 | 列表包含所有使用者的影片 |
| 17.4 | User 不可管理使用者 | User 訪問 `/users` | 頁面不顯示（或 403） |
