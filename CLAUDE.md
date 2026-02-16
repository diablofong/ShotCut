# ShotCut 專案指南

## 最高注意事項（CRITICAL）

### 語言設定
- **一律使用繁體中文回應**
- **即使自動清除 cache 後，仍必須使用繁體中文回應**
- 所有對話、註解、文件都使用繁體中文

### Git 提交規範
- **提交訊息不得包含任何 Claude Code 或 AI 的簽署**
- 不要加入 "Co-Authored-By: Claude" 或任何類似簽名
- 提交訊息必須簡潔明確，只描述變更內容

### 開發規範
- **開發一律強制嚴格採用 OpenSpec 方式開發**
- 使用 OpenSpec 工具：https://github.com/Fission-AI/OpenSpec
- OpenSpec 已全域安裝：`@fission-ai/openspec`
- 遵循 OpenSpec 的所有規範和最佳實踐
- 所有開發流程必須通過 OpenSpec 驗證

## 專案說明

ShotCut 是一個籃球比賽影片標記與片段擷取工具。

核心功能：
- 上傳比賽影片
- 音訊自動偵測候選時間點（哨音、歡呼聲）
- 快速標記與分類（進攻/防守/精彩/失誤）
- 標記球員編號
- 自動切出片段（FFmpeg）
- 依球員/標籤產出個人精華剪輯
- 分享連結給教練與家長

## 技術架構

- 前端：React + TypeScript + Vite + Tailwind CSS + Video.js
- 後端：Python + FastAPI + SQLite
- 影片處理：FFmpeg (ffmpeg-python)
- 音訊分析：librosa + scipy
