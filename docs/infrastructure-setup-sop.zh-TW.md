# ShotCut 雲端基礎設施申請 SOP

> **適用版本**：ShotCut v2.0（雲端版）
> **使用人數**：2 人
> **總費用**：$0（全部使用免費方案）
> **預計完成時間**：第一天可完成 Cloudflare 部分；Oracle VM 需等 1-7 天審核；eu.org 域名需等 1-4 週

---

## 架構總覽

```
使用者瀏覽器
  ├── shotcut.pages.dev  → Cloudflare Pages（前端，免費）
  ├── api.shotcut.eu.org → Cloudflare Tunnel → Oracle ARM A1（後端，免費）
  └── 影片傳輸          → Cloudflare R2（直接 Presigned URL，免費 10GB）
```

---

## 一、Cloudflare 帳號申請

**預計時間**：10 分鐘
**網址**：https://cloudflare.com

### 步驟

1. 前往 https://cloudflare.com，點選右上角 **Sign Up**
2. 輸入 Email 與密碼，完成 Email 驗證
3. 選擇 **Free** 方案（不需要信用卡）
4. 登入後進入 **Dashboard**

---

## 二、Cloudflare R2 Bucket 建立

**預計時間**：15 分鐘
**費用**：免費（10GB 儲存 + 每月 1000 萬次操作）

### 2.1 建立 Bucket

1. Cloudflare Dashboard 左側選單 → **R2 Object Storage**
2. 點選 **Create bucket**
3. 填入：
   - Bucket name：`shotcut-videos`
   - Location：**Asia Pacific（APAC）**
4. 點選 **Create bucket**

### 2.2 設定 CORS Policy

1. 進入 `shotcut-videos` bucket → 上方 **Settings** 頁籤
2. 找到 **CORS Policy** → 點選 **Add CORS policy**
3. 貼入以下設定：

```json
[
  {
    "AllowedOrigins": [
      "https://*.pages.dev",
      "http://localhost:5173"
    ],
    "AllowedMethods": ["PUT", "GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

4. 點選 **Save**

### 2.3 建立 API Token

1. R2 主頁右上角 → **Manage R2 API Tokens**
2. 點選 **Create API Token**
3. 填入：
   - Token name：`shotcut-app`
   - Permissions：**Object Read & Write**
   - Bucket：選擇 `shotcut-videos`（Specific bucket）
4. 點選 **Create API Token**
5. **立即記錄以下資訊（只顯示一次）**：

```
R2_ACCESS_KEY_ID=<顯示的 Access Key ID>
R2_SECRET_ACCESS_KEY=<顯示的 Secret Access Key>
```

### 2.4 記錄其他必要資訊

1. 回到 R2 主頁，右側找到 **Account ID**（32 位英數字串）
2. 進入 `shotcut-videos` bucket → **Settings** → 找到 **S3 API** 欄位

```
CLOUDFLARE_ACCOUNT_ID=<Account ID>
R2_BUCKET_NAME=shotcut-videos
R2_ENDPOINT_URL=https://<Account ID>.r2.cloudflarestorage.com
```

---

## 三、Cloudflare Pages 設定（前端 Hosting）

**預計時間**：10 分鐘
**產出**：前端自動部署網址 `https://shotcut-app.pages.dev`（或類似）

### 步驟

1. Cloudflare Dashboard 左側 → **Workers & Pages**
2. 點選 **Create** → 選擇 **Pages** → **Connect to Git**
3. 授權 GitHub，選擇 `ShotCut` repository
4. 設定 build：
   - **Framework preset**：Vite
   - **Build command**：`npm run build`
   - **Build output directory**：`dist`
   - **Root directory**：`frontend`
5. Environment Variables（點選 **Add variable**）：
   - `VITE_API_BASE_URL` = `http://YOUR_ORACLE_VM_IP:8000`（暫時，等 Tunnel 設定後更新）
6. 點選 **Save and Deploy**
7. 等待部署完成，記錄網址：

```
CLOUDFLARE_PAGES_URL=https://shotcut-app.pages.dev
```

---

## 四、Oracle Cloud 帳號申請

**預計時間**：15 分鐘申請，等待 1-7 天審核
**網址**：https://cloud.oracle.com/free

### 步驟

1. 前往 https://cloud.oracle.com/free，點選 **Start for free**
2. 填寫個人資訊：
   - Email、姓名
   - **Home Region**：選擇 **Japan East (Tokyo)**（最近、延遲最低）
3. 電話驗證（簡訊）
4. 信用卡驗證（**僅驗證用，不扣款**）
5. 提交後等待審核通知（Email 通知，通常 1-3 天）

### 常見問題

| 問題 | 解決方式 |
| ---- | ------- |
| 「Out of capacity」錯誤 | 換另一個 Availability Domain（AD-1/AD-2/AD-3）試試 |
| 帳號審核超過 7 天 | 聯繫 Oracle Support（免費方案有支援）|
| 信用卡被拒絕 | 嘗試不同的信用卡，或使用虛擬信用卡 |

---

## 五、Oracle ARM A1 VM 建立

**前提**：Oracle 帳號審核通過後執行
**預計時間**：20 分鐘

### 5.1 建立 VM Instance

1. Oracle Cloud Console → **Compute** → **Instances** → **Create instance**
2. 設定：
   - **Name**：`shotcut-server`
   - **Image**：Ubuntu 22.04 LTS
   - **Shape**：點選 **Change shape** → **Ampere（ARM）** → `VM.Standard.A1.Flex`
   - OCPU count：**4**（最大免費額度）
   - Memory：**24 GB**（最大免費額度）
3. **SSH Keys**：
   - 若無 SSH key，點選 **Generate a key pair for me** 並下載
   - 記錄私鑰路徑（例如：`~/.ssh/oracle_shotcut.key`）
4. 點選 **Create**
5. 等待狀態變為 **Running**，記錄：

```
ORACLE_VM_PUBLIC_IP=<Public IP address>
```

### 5.2 設定安全規則（Security List）

1. 進入 Instance 詳情頁 → **Primary VNIC** → **Subnet** → **Security List**
2. **Ingress Rules** → **Add Ingress Rules**：

| Source CIDR | Protocol | Port | 用途 |
| ----------- | -------- | ---- | ---- |
| 0.0.0.0/0 | TCP | 22 | SSH 管理 |

> **注意**：不需要開放 80/443，Cloudflare Tunnel 會處理，提高安全性。

### 5.3 連線並安裝 Docker

```bash
# SSH 連線
ssh -i ~/.ssh/oracle_shotcut.key ubuntu@<ORACLE_VM_PUBLIC_IP>

# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝 Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
newgrp docker

# 安裝 Docker Compose plugin
sudo apt install -y docker-compose-plugin

# 驗證安裝
docker --version
docker compose version
```

---

## 六、eu.org 免費域名申請

**預計時間**：15 分鐘申請，等待 1-4 週審核
**網址**：https://nic.eu.org

### 步驟

1. 前往 https://nic.eu.org，點選 **Register** 建立帳號
2. 登入後點選 **Domains** → **Create new domain**
3. 填入希望的域名，例如：
   - `shotcut.eu.org`
   - `shotcut-app.eu.org`
   - `myshotcut.eu.org`
4. Name Servers 選擇 **Use Cloudflare's nameservers**：
   - `aria.ns.cloudflare.com`
   - `norm.ns.cloudflare.com`
   > 這些值在 Cloudflare 加入域名後可取得，見下一步
5. 提交申請，等待審核 Email

### 6.1 Cloudflare 先加入域名（等 eu.org 批准前）

1. Cloudflare Dashboard → **Add a domain**
2. 輸入 `shotcut.eu.org`
3. 選擇 **Free** 方案
4. 記錄 Cloudflare 提供的 nameserver：

```
ns1: aria.ns.cloudflare.com
ns2: norm.ns.cloudflare.com
```

5. 回到 eu.org 申請填入上述 nameserver

---

## 七、Cloudflare Tunnel 設定

**前提**：eu.org 域名審核通過 + Oracle VM 已建立
**預計時間**：20 分鐘

### 7.1 在 Oracle VM 安裝 cloudflared

```bash
# SSH 連線到 VM
ssh -i ~/.ssh/oracle_shotcut.key ubuntu@<ORACLE_VM_PUBLIC_IP>

# 安裝 cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# 驗證
cloudflared --version
```

### 7.2 建立 Tunnel

1. Cloudflare Dashboard → **Zero Trust** → **Networks** → **Tunnels**
2. 點選 **Create a tunnel** → 選擇 **Cloudflared**
3. Tunnel name：`shotcut-tunnel`
4. 點選 **Save tunnel**
5. 複製顯示的安裝指令（含 token），在 VM 執行：

```bash
# VM 上執行（Cloudflare 會提供完整指令）
sudo cloudflared service install <YOUR_TUNNEL_TOKEN>
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

### 7.3 設定 Public Hostname

1. Tunnel 詳情頁 → **Public Hostname** → **Add a public hostname**
2. 設定：
   - Subdomain：`api`
   - Domain：`shotcut.eu.org`
   - Service Type：**HTTP**
   - URL：`localhost:8000`
3. 點選 **Save hostname**

### 7.4 更新 Cloudflare Pages 環境變數

1. Pages 專案設定 → **Environment variables**
2. 更新：`VITE_API_BASE_URL` = `https://api.shotcut.eu.org`
3. 重新部署（Deployments → Retry deployment）

---

## 八、等待期間暫代方案

**當 eu.org 審核中（最長 4 週）**，可用 Oracle VM IP 直連：

```bash
# 前端 .env.local（本地開發）
VITE_API_BASE_URL=http://<ORACLE_VM_PUBLIC_IP>:8000

# Oracle VM Security List 暫時開放 Port 8000
# （eu.org 設定好 Tunnel 後可關閉）
```

---

## 九、環境變數彙整

申請完成後，將以下值填入 Oracle VM 的 `.env` 檔案：

```env
# 資料庫
DATABASE_URL=mysql+aiomysql://shotcut:YOUR_DB_PASSWORD@db:3306/shotcut
MYSQL_ROOT_PASSWORD=YOUR_ROOT_PASSWORD
MYSQL_DATABASE=shotcut
MYSQL_USER=shotcut
MYSQL_PASSWORD=YOUR_DB_PASSWORD

# 安全性
SECRET_KEY=（執行 python -c "import secrets; print(secrets.token_urlsafe(32))" 生成）

# 管理員帳號
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YOUR_ADMIN_PASSWORD

# 儲存設定（R2）
STORAGE_BACKEND=r2
R2_ACCESS_KEY_ID=（來自步驟二）
R2_SECRET_ACCESS_KEY=（來自步驟二）
R2_BUCKET_NAME=shotcut-videos
R2_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com

# Feature Flags（雲端版關閉）
ENABLE_CLIPS=false
ENABLE_HIGHLIGHTS=false
ENABLE_SHARING=false

# CORS（允許 Pages 網址）
CORS_ORIGINS=https://shotcut-app.pages.dev
IS_PRODUCTION=true
```

---

## 十、驗證清單

```text
Cloudflare
  □ R2 bucket 建立完成
  □ CORS Policy 設定完成
  □ API Token 建立並記錄
  □ Pages 部署成功，能訪問 shotcut.pages.dev

Oracle Cloud
  □ 帳號審核通過
  □ ARM A1 VM 建立，狀態 Running
  □ SSH 連線正常
  □ Docker 安裝完成

域名 & Tunnel
  □ eu.org 申請送出
  □ Cloudflare 域名加入
  □ cloudflared 在 VM 上執行
  □ api.shotcut.eu.org 能連到 VM:8000

整合測試
  □ 前端可以登入（shotcut.pages.dev）
  □ 影片上傳到 R2 成功
  □ 影片播放正常（302 redirect）
```
