# BananaDB Python 3.13 安裝與虛擬環境設定指引

## 步驟 1：下載並安裝 Python 3.13

### 自動下載（推薦）

執行以下 PowerShell 命令自動下載並啟動安裝程式：

```powershell
# 下載 Python 3.13.11
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.13.11/python-3.13.11-amd64.exe" -OutFile "$env:TEMP\python-3.13.11-amd64.exe"

# 啟動安裝程式
Start-Process "$env:TEMP\python-3.13.11-amd64.exe"
```

### 手動下載

前往以下連結下載：
https://www.python.org/ftp/python/3.13.11/python-3.13.11-amd64.exe

### ⚠️ 安裝時的重要設定

在安裝過程中，請確保：
1. ✅ **勾選「Add Python 3.13 to PATH」**（非常重要！）
2. ✅ **勾選「Install for all users」**（建議）
3. ✅ 選擇「Customize installation」→ 勾選「py launcher」

---

## 步驟 2：驗證 Python 3.13 安裝

安裝完成後，**重新開啟 PowerShell**，執行：

```powershell
py -3.13 --version
```

應顯示：`Python 3.13.11`

---

## 步驟 3：建立虛擬環境

在專案目錄執行：

```powershell
cd c:\Users\hende\Documents\gemini\prompt_database_V2

# 建立虛擬環境（使用 Python 3.13）
py -3.13 -m venv venv
```

---

## 步驟 4：啟用虛擬環境

### PowerShell（推薦）

```powershell
.\venv\Scripts\Activate.ps1
```

**若遇到執行政策錯誤，請執行：**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

執行成功後，命令提示字元前方會顯示 `(venv)`。

---

## 步驟 5：安裝專案套件

在虛擬環境中（確認有 `(venv)` 前綴）：

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 步驟 6：啟動 BananaDB 伺服器

```powershell
python app.py
```

或使用 uvicorn：

```powershell
python -m uvicorn app:app --reload --port 8000
```

---

## 步驟 7：停用虛擬環境（可選）

完成工作後，可停用虛擬環境：

```powershell
deactivate
```

---

## 快速參考

### 每次啟動 BananaDB 的流程：

```powershell
# 1. 進入專案目錄
cd c:\Users\hende\Documents\gemini\prompt_database_V2

# 2. 啟用虛擬環境
.\venv\Scripts\Activate.ps1

# 3. 啟動伺服器
python app.py
```

### 檢查當前 Python 版本：

```powershell
python --version  # 應顯示 Python 3.13.11（在虛擬環境中）
```

---

## 疑難排解

### 問題：`py -3.13` 找不到

**解決方案：**
- 確認已重新開啟 PowerShell
- 檢查 Python 3.13 是否正確安裝：`py --list`
- 重新安裝 Python 3.13，確保勾選「Add to PATH」

### 問題：無法執行 Activate.ps1

**解決方案：**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 問題：虛擬環境啟用後仍顯示 Python 3.14

**解決方案：**
- 停用虛擬環境：`deactivate`
- 刪除虛擬環境：`Remove-Item -Recurse -Force venv`
- 重新建立：`py -3.13 -m venv venv`

---

## 完成！

設定完成後，請前往 http://localhost:8000 開始使用 BananaDB。
