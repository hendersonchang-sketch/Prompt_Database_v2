"""
診斷翻譯功能的測試腳本
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# 載入環境變數
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print("=" * 60)
print("🔍 診斷 Gemini API 與翻譯功能")
print("=" * 60)

# 1. 檢查 API Key
print(f"\n1️⃣ API Key 狀態:")
if GEMINI_API_KEY:
    print(f"   ✅ 已設定（前10字元: {GEMINI_API_KEY[:10]}...）")
else:
    print("   ❌ 未設定 GEMINI_API_KEY")
    exit(1)

# 2. 測試 Gemini API 基本功能
print(f"\n2️⃣ 測試 Gemini API 基本功能:")
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Say hello in Traditional Chinese")
    print(f"   ✅ API 正常運作")
    print(f"   回應: {response.text}")
except Exception as e:
    print(f"   ❌ API 失敗: {e}")
    exit(1)

# 3. 測試翻譯功能
print(f"\n3️⃣ 測試翻譯功能:")
try:
    from ai_engine import translate_prompt
    
    test_text = "high-end studio portrait"
    print(f"   輸入: {test_text}")
    
    result = translate_prompt(test_text)
    
    print(f"   輸出:")
    print(f"     - English: {result.get('english', '')}")
    print(f"     - Chinese: {result.get('chinese', '')}")
    
    if result.get('chinese'):
        print("   ✅ 翻譯成功")
    else:
        print("   ❌ 中文欄位為空")
        
except Exception as e:
    print(f"   ❌ 翻譯失敗: {e}")
    import traceback
    traceback.print_exc()

# 4. 測試 Tags 提取
print(f"\n4️⃣ 測試 Tags 提取:")
try:
    from ai_engine import extract_tags_from_text
    
    test_text = "high-end studio portrait"
    print(f"   輸入: {test_text}")
    
    tags, category = extract_tags_from_text(test_text)
    
    print(f"   輸出:")
    print(f"     - Tags: {tags}")
    print(f"     - Category: {category}")
    
    # 檢查是否有中文 tags
    import re
    has_chinese = any(re.search(r'[\u4e00-\u9fff]', tag) for tag in tags)
    
    if has_chinese:
        print("   ✅ Tags 包含中文")
    else:
        print("   ❌ Tags 缺少中文")
        
except Exception as e:
    print(f"   ❌ Tags 提取失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("診斷完成")
print("=" * 60)
