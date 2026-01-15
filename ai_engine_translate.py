"""
BananaDB AI 分析引擎
使用 Google Gemini 2.0 Flash Vision 逆向工程提示詞
"""
import os
import json
from typing import Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv


# 載入環境變數
load_dotenv()

# 設定 Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ 錯誤：未設定 GEMINI_API_KEY 環境變數")

genai.configure(api_key=GEMINI_API_KEY)


# System Prompt for Banana Pro 風格分析
BANANA_PRO_SYSTEM_PROMPT = """You are an expert in the 'Banana Pro' Stable Diffusion model. Analyze the uploaded image.

Extract or reverse-engineer the Positive Prompt (English). Focus on lighting, camera angle, and art style.
Translate the prompt into descriptive Traditional Chinese (Taiwan usage).
Suggest a standard Negative Prompt for this style.
Generate 3-5 relevant tags.

Return strict JSON format:
{
  "positive_prompt": "...",
  "positive_prompt_zh": "...",
  "negative_prompt": "...",
  "tags": ["tag1", "tag2", "tag3"]
}

IMPORTANT: Your response must be ONLY valid JSON. Do not include any markdown code blocks or explanations."""


def translate_prompt(text: str) -> Dict[str, str]:
    """
    自動偵測並翻譯 prompt
    - 如果是英文，翻譯成繁體中文
    - 如果是中文，翻譯成英文
    - 超長 prompt 生成摘要
    
    Args:
        text: 要翻譯的文字
    
    Returns:
        包含 'english' 和 'chinese' 的字典
    """
    try:
        # 超長 prompt：保留原文 + 生成中文摘要
        if len(text) > 1000:
            print(f"📄 Prompt 較長 ({len(text)} 字元)，生成中文摘要")
            import re
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
            
            if has_chinese:
                print("➡️ 偵測到中文，保留原文")
                return {'english': '', 'chinese': text}
            
            # 生成中文摘要
            try:
                model = genai.GenerativeModel('gemini-2.0-flash')
                summary_prompt = f"""請用繁體中文總結這個 AI 圖片生成指令（100-200字），包含：主題、關鍵元素、重要設定、風格。

指令內容（前2000字元）：
{text[:2000]}

只輸出繁體中文摘要，不要其他格式或解釋。"""

                response = model.generate_content(summary_prompt)
                chinese_summary = response.text.strip().replace('"', '').replace('`', '').replace('*', '')
                
                print(f"✅ 摘要生成: {chinese_summary[:80]}...")
                return {'english': text, 'chinese': chinese_summary}
            except Exception as e:
                print(f"⚠️ 摘要失敗: {e}")
                return {'english': text, 'chinese': '（Prompt過長，摘要生成失敗）'}
        
        # 正常長度：翻譯
        print(f"🔄 開始翻譯 ({len(text)} 字元)")
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""Translate: {text}

Rules:
- English → Traditional Chinese (Taiwan)
- Simplified Chinese → keep as-is, translate to English  
- Traditional Chinese → keep as-is, translate to English

JSON output only:
{{"english": "...", "chinese": "..."}}"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # 清理 markdown
        for marker in ["```json", "```"]:
            if response_text.startswith(marker):
                response_text = response_text[len(marker):]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # 提取 JSON
        import re
        json_match = re.search(r'\{[^{}]*"english"[^{}]*"chinese"[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        result = json.loads(response_text)
        english = result.get('english', '').strip()
        chinese = result.get('chinese', '').strip()
        
        # 驗證
        if 'Output (JSON only):' in english or 'Output (JSON only):' in chinese:
            english = ''
            chinese = ''
        
        if english or chinese:
            print(f"✅ 翻譯成功")
            return {'english': english or text, 'chinese': chinese}
        
        raise ValueError("Translation empty")
        
    except Exception as e:
        print(f"❌ 翻譯失敗: {type(e).__name__}: {e}")
        import re
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
        return {'english': '', 'chinese': text} if has_chinese else {'english': text, 'chinese': ''}
