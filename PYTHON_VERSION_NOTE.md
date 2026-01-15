# Python 3.14 相容性問題說明

## 問題

Python 3.14.0 是開發中的版本（目前為 Alpha/Beta），Pydantic 和 FastAPI 尚未完全支援。

錯誤訊息：
```
TypeError: Metaclasses with custom tp_new are not supported.
```

## 解決方案選項

### 選項 1：使用 Python 3.13 或 3.12（推薦）

1. 下載並安裝 Python 3.13 或 3.12：
   - Python 3.13: https://www.python.org/downloads/
   - Python 3.12: https://www.python.org/downloads/release/python-3120/

2. 使用虛擬環境隔離 Python 版本：
   ```powershell
   # 使用 Python 3.13 建立虛擬環境
   py -3.13 -m venv venv
   
   # 啟用虛擬環境
   .\venv\Scripts\Activate.ps1
   
   # 安裝套件
   pip install -r requirements.txt
   
   # 啟動伺服器
   python app.py
   ```

### 選項 2：等待套件更新

等待 Pydantic 和 FastAPI 官方支援 Python 3.14（通常需要數週到數月）。

### 選項 3：暫時繼續使用系統的 Python 3.14（實驗性）

某些功能可能可以透過環境變數暫時繞過，但不保證穩定性：

```powershell
$env:PYTHONMALLOC="malloc"
python app.py
```

---

## 建議

**強烈建議使用選項 1**：安裝 Python 3.12 或 3.13，並使用虛擬環境。
Python 3.14 是開發版本，不適合用於生產環境或穩定專案。
