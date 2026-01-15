# 🔐 API Key 安全指南

## ⚠️ 重要：保護您的 API Key

API Key 就像您家的鑰匙，**絕對不能**分享或公開！

## ✅ 正確的做法

### 1. 使用環境變數
```bash
# .env 檔案（已在 .gitignore 中）
GEMINI_API_KEY=your_actual_api_key_here
```

### 2. 永遠不要做的事情
- ❌ 不要將 `.env` 檔案提交到 Git
- ❌ 不要在 `.env.example` 中放真實的 API Key
- ❌ 不要在程式碼中硬編碼 API Key
- ❌ 不要在截圖中顯示 API Key
- ❌ 不要在公開的文件中分享 API Key

### 3. 檢查 .gitignore
確保以下檔案在 `.gitignore` 中：
```gitignore
.env
.env.local
*.env
```

### 4. 使用 .env.example 作為範本
```bash
# .env.example（可安全提交到 Git）
GEMINI_API_KEY=your_api_key_here
```

## 🛡️ 如何設定（新使用者）

1. 複製範本：
   ```bash
   cp .env.example .env
   ```

2. 前往 Google AI Studio 取得 API Key：
   https://aistudio.google.com/app/apikey

3. 編輯 `.env` 檔案：
   ```bash
   GEMINI_API_KEY=你的真實金鑰
   ```

4. 驗證 `.env` 不在 Git 追蹤中：
   ```bash
   git check-ignore .env
   # 應該顯示：.env
   ```

## 🚨 如果 API Key 洩漏了

1. **立即撤銷舊的 Key**
   - 訪問：https://aistudio.google.com/app/apikey
   - 找到洩漏的 Key 並刪除

2. **生成新的 Key**
   - 點擊「Create API Key」
   - 複製新的 Key

3. **更新 `.env` 檔案**
   ```bash
   GEMINI_API_KEY=新的金鑰
   ```

4. **檢查 Git 歷史記錄**
   ```bash
   # 搜尋是否有 API Key 在 Git 中
   git log -p | grep -i "AIza"
   ```

5. **如果需要清除 Git 歷史**
   ```bash
   # 使用 BFG Repo-Cleaner 或 git filter-branch
   # 這會重寫 Git 歷史！謹慎使用
   ```

## ✅ 安全檢查清單

在每次提交前：
- [ ] `.env` 在 `.gitignore` 中
- [ ] `.env.example` 只包含佔位符
- [ ] `git status` 確認 `.env` 未被追蹤
- [ ] 程式碼中沒有硬編碼的 API Key
- [ ] 沒有在註解中提到真實的 Key

## 📚 更多資訊

- [Google API Key 最佳實踐](https://cloud.google.com/docs/authentication/api-keys)
- [Git Secrets 防洩漏工具](https://github.com/awslabs/git-secrets)
