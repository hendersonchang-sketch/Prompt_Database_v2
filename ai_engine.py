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
    - 短 prompt: 完整翻譯
    - 長 prompt (>1000字): 保留原文 + 生成中文摘要
    
    Args:
        text: 要翻譯的文字
    
    Returns:
        包含 'english' 和 'chinese' 的字典
    """
    try:
        import re
        
        # 超長 prompt：保留原文 + 生成中文摘要
        if len(text) > 1000:
            print(f"📄 Prompt 較長 ({len(text)} 字元)，生成中文摘要")
            
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
            
            if has_chinese:
                print("➡️ 偵測到中文，保留原文")
                return {'english': '', 'chinese': text}
            
            # 生成中文摘要
            try:
                model = genai.GenerativeModel('gemini-2.0-flash')
                summary_prompt = f"""請用簡潔的繁體中文總結這個 AI 圖片生成指令（約150字內），包含：
- 主題或主要內容
- 關鍵視覺元素
- 風格或氛圍

指令內容（前2000字元）：
{text[:2000]}

只輸出繁體中文摘要，不要引號或其他格式。"""

                response = model.generate_content(summary_prompt)
                chinese_summary = response.text.strip()
                
                # 清理格式
                chinese_summary = chinese_summary.replace('"', '').replace('`', '').replace('*', '').strip()
                if chinese_summary.startswith('```'):
                    lines = chinese_summary.split('\n')
                    chinese_summary = '\n'.join(lines[1:-1]) if len(lines) > 2 else chinese_summary
                chinese_summary = chinese_summary.strip()
                
                print(f"✅ 摘要生成: {chinese_summary[:80]}...")
                return {'english': text, 'chinese': chinese_summary}
                
            except Exception as e:
                print(f"⚠️ 摘要生成失敗: {e}")
                import traceback
                traceback.print_exc()
                return {'english': text, 'chinese': '（Prompt 過長，摘要生成失敗）'}
        
        # 正常長度：完整翻譯
        print(f"🔄 開始翻譯 ({len(text)} 字元)")
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""翻譯這段文字：

{text}

規則：
- 英文 → 繁體中文（台灣用語）
- 簡體中文 → 保持原樣，翻譯成英文
- 繁體中文 → 保持原樣，翻譯成英文

只輸出 JSON：
{{"english": "...", "chinese": "..."}}"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # 清理 markdown
        for marker in ["```json", "```"]:
            if response_text.startswith(marker):
                response_text = response_text[len(marker):].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()
        
        # 提取 JSON
        json_match = re.search(r'\{[^{}]*"english"[^{}]*"chinese"[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        result = json.loads(response_text)
        english = result.get('english', '').strip()
        chinese = result.get('chinese', '').strip()
        
        if english or chinese:
            print(f"✅ 翻譯成功")
            return {'english': english or text, 'chinese': chinese}
        
        raise ValueError("Translation empty")
        
    except Exception as e:
        print(f"❌ 翻譯失敗: {type(e).__name__}: {e}")
        import re
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
        return {'english': '', 'chinese': text} if has_chinese else {'english': text, 'chinese': ''}


def analyze_image(image_path: str, context_text: str = "") -> Dict[str, Any]:
    """
    使用 Gemini 2.0 Flash Vision 分析圖片並逆向工程提示詞
    
    Args:
        image_path: 圖片檔案路徑
        context_text: 額外的上下文資訊（選填）
    
    Returns:
        包含 positive_prompt, positive_prompt_zh, negative_prompt, tags 的字典
    """
    try:
        # 使用 Gemini 2.0 Flash 模型（穩定版本，支援視覺分析）
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # 使用 PIL 讀取並上傳圖片（自動處理各種格式）
        from PIL import Image
        image = Image.open(image_path)
        
        # 準備提示詞
        prompt_parts = [BANANA_PRO_SYSTEM_PROMPT]
        if context_text:
            prompt_parts.append(f"\nAdditional context: {context_text}")
        
        # 呼叫 Gemini API（直接傳入 PIL Image 物件）
        response = model.generate_content(
            [prompt_parts[0], image] + (prompt_parts[1:] if len(prompt_parts) > 1 else [])
        )
        
        # 解析 JSON 回應
        response_text = response.text.strip()
        
        # 移除可能的 Markdown 程式碼區塊標記
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # 解析 JSON
        result = json.loads(response_text)
        
        # 驗證必要欄位
        required_fields = ["positive_prompt", "positive_prompt_zh", "negative_prompt", "tags"]
        for field in required_fields:
            if field not in result:
                result[field] = "" if field != "tags" else []
        
        # 確保 tags 是陣列
        if not isinstance(result["tags"], list):
            result["tags"] = []
        
        print(f"✅ AI 分析完成: {image_path}")
        return result
        
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 解析錯誤: {e}")
        print(f"原始回應: {response_text}")
        # 回傳預設值
        return {
            "positive_prompt": "Unable to analyze image",
            "positive_prompt_zh": "無法分析圖片",
            "negative_prompt": "low quality, blurry",
            "tags": ["error"]
        }
    
    except Exception as e:
        print(f"❌ AI 分析失敗: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        # 回傳預設值
        return {
            "positive_prompt": "Error during analysis",
            "positive_prompt_zh": "分析過程發生錯誤",
            "negative_prompt": "low quality, blurry",
            "tags": ["error"]
        }


if __name__ == "__main__":
    # 測試分析功能（需要實際圖片檔案）
    import sys
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        result = analyze_image(test_image)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法: python ai_engine.py <圖片路徑>")
