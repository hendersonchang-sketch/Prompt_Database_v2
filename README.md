# 🍌 BananaDB - 本地 AI 圖片資料庫與提示詞逆向工程系統

一個完整的本地 Web 應用程式，用於收集、分析與儲存 AI 圖片提示詞。

## ✨ 功能特色

- 🖱️ **Chrome 右鍵選單收集**：透過瀏覽器擴充功能一鍵儲存網頁圖片
- 📤 **拖放上傳**：直覺的檔案上傳介面
- 🤖 **AI 分析**：使用 Google Gemini 2.0 Flash Vision 逆向工程提示詞
- 🌏 **雙語支援**：自動產生英文 + 繁體中文提示詞
- 🎨 **美觀介面**：深色主題 + 瀑布流布局
- 📋 **一鍵複製**：輕鬆複製提示詞供後續使用

## 🚀 快速開始

### 1. 環境準備

確保已安裝 Python 3.10+

### 2. 安裝相依性套件

```powershell
cd c:\Users\hende\Documents\gemini\prompt_database_V2
pip install -r requirements.txt
```

### 3. 設定 Gemini API 金鑰

建立 `.env` 檔案（可參考 `.env.example`）：

```
GEMINI_API_KEY=your-gemini-api-key-here
```

### 4. 啟動後端伺服器

```powershell
python -m uvicorn app:app --reload --port 8000
```

或直接執行：

```powershell
python app.py
```

伺服器將在 `http://localhost:8000` 啟動

### 5. 安裝 Chrome 擴充功能

1. 開啟 Chrome 瀏覽器
2. 前往 `chrome://extensions/`
3. 開啟「開發人員模式」（右上角）
4. 點擊「載入未封裝項目」
5. 選擇 `c:\Users\hende\Documents\gemini\prompt_database_V2\extension` 資料夾

### 6. 開始使用

- 前往 `http://localhost:8000/` 查看 Web UI
- 在任意網頁右鍵點擊圖片 → 選擇「🍌 Save to BananaDB」
- 或直接拖放圖片至 Web UI 上傳

## 📁 專案結構

```
prompt_database_V2/
├── app.py                  # FastAPI 主應用程式
├── database.py             # SQLite 資料庫邏輯
├── ai_engine.py            # Gemini Vision API 整合
├── requirements.txt        # Python 套件相依性
├── .env                    # 環境變數（需手動建立）
├── .env.example            # 環境變數範例
├── bananadb.db             # SQLite 資料庫（自動建立）
├── uploads/                # 圖片儲存資料夾（自動建立）
├── extension/              # Chrome 擴充功能
│   ├── manifest.json
│   └── background.js
└── templates/              # 前端 HTML
    └── index.html
```

## 🛠️ API 端點

### POST `/api/collect_url`
從 URL 收集圖片並分析

**請求：**
```json
{
  "image_url": "https://example.com/image.jpg",
  "page_url": "https://example.com",
  "context_text": "optional context"
}
```

### POST `/api/upload`
上傳本地圖片並分析

**請求：** `multipart/form-data`

### GET `/api/images`
查詢所有圖片記錄

**回應：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "filename": "abc123.jpg",
      "positive_prompt": "...",
      "positive_prompt_zh": "...",
      "negative_prompt": "...",
      "tags": ["tag1", "tag2"],
      "source_url": "...",
      "created_at": "2026-01-15 07:30:00"
    }
  ]
}
```

## 🎯 使用提示

1. **Gemini API 配額**：免費方案有 API 呼叫限制，請注意用量
2. **圖片下載限制**：部分網站（如 Twitter/Facebook）可能封鎖圖片下載，若遇到失敗可嘗試手動下載後上傳
3. **AI 分析時間**：每張圖片分析約需 5-15 秒，請耐心等候

## 🐛 疑難排解

### 錯誤：`GEMINI_API_KEY` 未設定
確認已建立 `.env` 檔案並填入 API 金鑰

### 圖片下載失敗
部分網站有反爬蟲機制，請嘗試手動下載後上傳

### Chrome 擴充功能無回應
確認後端伺服器正在執行（`http://localhost:8000`）

## 📝 授權條款

MIT License

---

**建立者**: 台灣資深首席軟體架構師 🇹🇼
