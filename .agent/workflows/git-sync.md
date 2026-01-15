---
description: 安全地同步程式碼到 GitHub（防止 API Key 洩漏）
---

# Git 安全同步流程

這個 workflow 確保你在提交程式碼到 GitHub 之前，API Key 等敏感資訊不會洩漏。

## 前置檢查（每次提交前必做）

### 1. 檢查敏感檔案是否被 gitignore
```bash
git check-ignore .env
# 應該顯示：.env（表示已被忽略）

git check-ignore .env.local
# 應該顯示：.env.local
```

### 2. 檢查 .env.example 是否安全
```bash
cat .env.example | grep "GEMINI_API_KEY"
# 應該只看到：GEMINI_API_KEY=your_api_key_here
# 不應該有任何以 "AIza" 開頭的真實金鑰
```

### 3. 檢查 git status
```bash
git status
# 確保 .env 沒有出現在「Changes to be committed」或「Untracked files」中
```

### 4. 掃描暫存區是否有 API Key
```bash
git diff --cached | grep -i "AIza"
# 應該沒有任何輸出（如果有輸出，表示有 API Key 被暫存）
```

## 標準同步流程

### 步驟 1：查看變更
```bash
git status
```

### 步驟 2：暫存檔案
```bash
# 只暫存需要的檔案（不要用 git add .）
git add ai_engine.py
git add templates/index.html
git add README.md

# 或者使用互動模式
git add -p
```

### 步驟 3：再次檢查（安全驗證）
```bash
# 檢查暫存內容
git diff --cached

# 搜尋是否有 API Key
git diff --cached | grep -i "GEMINI_API_KEY"
git diff --cached | grep -i "AIza"
```

### 步驟 4：提交
```bash
git commit -m "描述你的變更"
```

### 步驟 5：推送前最終檢查
```bash
# 查看將要推送的內容
git log -p origin/main..HEAD

# 確保沒有敏感資訊
git log -p origin/main..HEAD | grep -i "AIza"
```

### 步驟 6：推送到 GitHub
```bash
git push origin main
```

## 🚨 緊急處理：如果不小心提交了 API Key

### 方法 1：如果還沒 push（本地提交）
```bash
# 撤銷最後一次提交（保留變更）
git reset --soft HEAD~1

# 修正問題檔案
# 編輯 .env.example，移除真實 API Key

# 重新提交
git add .env.example
git commit -m "修正：移除真實 API Key"
```

### 方法 2：如果已經 push（已經在 GitHub）
1. **立即撤銷舊的 API Key**
   - 訪問：https://aistudio.google.com/app/apikey
   - 刪除洩漏的 Key
   - 生成新的 Key

2. **從 Git 歷史中移除**
   ```bash
   # 使用 git filter-branch（謹慎使用！）
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env.example" \
     --prune-empty --tag-name-filter cat -- --all

   # 或使用 BFG Repo-Cleaner（更快速）
   # 下載：https://rtyley.github.io/bfg-repo-cleaner/
   java -jar bfg.jar --replace-text passwords.txt
   ```

3. **強制推送（這會重寫歷史）**
   ```bash
   git push origin --force --all
   ```

## ✅ 安全檢查清單

每次提交前，確認：
- [ ] `.env` 在 `.gitignore` 中
- [ ] `.env` 沒有在 `git status` 中出現
- [ ] `.env.example` 只包含 `your_api_key_here`
- [ ] 程式碼中沒有硬編碼的 API Key
- [ ] `git diff --cached` 沒有顯示 "AIza" 字樣
- [ ] 資料庫檔案 `*.db` 在 `.gitignore` 中
- [ ] 上傳目錄 `uploads/` 在 `.gitignore` 中

## 自動化安全檢查（可選）

### 安裝 git-secrets
```bash
# macOS
brew install git-secrets

# Windows (使用 Git Bash)
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets
./install.sh
```

### 設定專案
```bash
cd /path/to/prompt_database_V2

# 初始化 git-secrets
git secrets --install

# 添加 API Key 模式
git secrets --add 'AIza[a-zA-Z0-9_-]{35}'
git secrets --add 'GEMINI_API_KEY=AIza.*'

# 掃描當前提交
git secrets --scan

# 掃描整個歷史
git secrets --scan-history
```

## 📚 參考資源

- [API_KEY_SECURITY.md](../API_KEY_SECURITY.md) - 完整安全指南
- [Git Secrets](https://github.com/awslabs/git-secrets) - 自動防洩漏工具
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) - 清理 Git 歷史
