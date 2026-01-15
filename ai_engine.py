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

CRITICAL REQUIREMENTS:
1. Extract or reverse-engineer the Positive Prompt (English)
2. MUST translate the prompt into Traditional Chinese (Taiwan usage) - this is MANDATORY
3. Generate 5-8 tags in BOTH English AND Traditional Chinese (mixed together in one array)
4. Classify into ONE category
5. Suggest a Negative Prompt

Focus on lighting, camera angle, and art style.

Available Categories:
- Portrait (人像/肖像) - for people photos, portraits
- Landscape (風景) - for nature, scenery, cityscapes
- Animal (動物) - for pets, wildlife
- Architecture (建築) - for buildings, interiors
- Sci-Fi (科幻) - for futuristic, robots, space
- Art (藝術/插畫) - for abstract art, illustrations
- Food (食物) - for cuisine, dishes
- Fashion (時尚) - for clothing, accessories
- Other (其他) - for anything else

Tags Example: ["3D", "三維", "isometric", "等距視角", "miniature", "微縮模型", "gym", "健身房", "Porsche", "保時捷"]

Return STRICT JSON format (no markdown, no explanations):
{
  "positive_prompt": "detailed English prompt here...",
  "positive_prompt_zh": "完整的繁體中文翻譯在這裡...",
  "negative_prompt": "low quality, blurry, ...",
  "tags": ["english_tag", "中文標籤", "another_tag", "另一個標籤", ...],
  "category": "Architecture"
}

CRITICAL: You MUST include positive_prompt_zh (Traditional Chinese translation). Tags MUST mix English and Chinese. Response must be ONLY valid JSON."""


def extract_tags_from_text(text: str) -> tuple[list[str], str]:
    """
    從文字中提取關鍵字作為 tags 並判斷分類
    使用 Gemini 智慧提取，同時生成中英雙語標籤與分類
    
    Args:
        text: 要提取標籤的文字
    
    Returns:
        (tags列表, category字串) 的 tuple
    """
    try:
        # 截斷過長文字
        text_sample = text[:1000] if len(text) > 1000 else text
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""Extract 5-8 relevant keywords/tags from this AI image prompt.
Generate tags in BOTH English and Traditional Chinese (mixed in one array).
Also classify into ONE category: Portrait, Landscape, Animal, Architecture, Sci-Fi, Art, Food, Fashion, or Other.

Text:
{text_sample}

Output JSON only:
{{"tags": ["english_tag1", "中文標籤1", "english_tag2", "中文標籤2", ...], "category": "Portrait"}}"""

        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # 清理 JSON
        for marker in ["```json", "```"]:
            if text.startswith(marker):
                text = text[len(marker):].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        
        result = json.loads(text)
        tags = result.get("tags", [])
        category = result.get("category", "Other")
        
        print(f"✅ 提取 tags: {tags}, 分類: {category}")
        return (tags[:10], category)  # 限制最多 10 個 tags
        
    except Exception as e:
        print(f"⚠️ Tags 提取失敗: {e}")
        # 簡單回退：用逗號或空格分割
        import re
        words = re.findall(r'\b\w{3,}\b', text[:200])
        return (words[:5] if words else ["未分類", "uncategorized"], "Other")


def translate_prompt(text: str) -> Dict[str, str]:
    """
    自動偵測並翻譯 prompt
    - 短 prompt: 完整翻譯
    - 長 prompt (>1000字): 保留原文 + 簡化說明
    
    Args:
        text: 要翻譯的文字
    
    Returns:
        包含 'english' 和 'chinese' 的字典
    """
    import re
    
    # 超長 prompt：保留原文 + 簡化說明
    if len(text) > 1000:
        print(f"📄 Prompt 較長 ({len(text)} 字元)")
        
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
        
        if has_chinese:
            print("➡️ 偵測到中文，保留原文")
            return {'english': '', 'chinese': text}
        
        # 英文長 prompt：簡化說明
        print("➡️ Prompt 過長，保留完整英文，中文欄位顯示簡化說明")
        
        # 提取關鍵詞
        clean = re.sub(r'<[^>]+>', '', text[:300])
        clean = re.sub(r'[{}()\[\]"\'<>]', ' ', clean)
        words = re.findall(r'\b[A-Za-z]{4,}\b', clean)
        keywords = ' '.join(words[:8])
        
        chinese_note = f"長指令 - 主題關鍵字：{keywords}"
        return {'english': text, 'chinese': chinese_note}
    
    # 正常長度：完整翻譯
    print(f"🔄 開始翻譯 ({len(text)} 字元)")
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # 超級簡化的 prompt
        prompt = f"""Translate this text to Traditional Chinese (Taiwan):

{text}

IMPORTANT: 
- Output ONLY the Traditional Chinese translation
- Do NOT include the original English
- Do NOT use any markdown or code blocks"""

        print(f"📤 發送翻譯請求...")
        response = model.generate_content(prompt)
        chinese_text = response.text.strip()
        
        print(f"📥 收到回應: {chinese_text[:100]}...")
        
        # 清理可能的 markdown
        chinese_text = chinese_text.replace('```', '').replace('`', '').strip()
        
        # 驗證是否真的是中文
        if re.search(r'[\u4e00-\u9fff]', chinese_text):
            print(f"✅ 翻譯成功（偵測到中文字元）")
            return {'english': text, 'chinese': chinese_text}
        else:
            print(f"⚠️ 回應不包含中文，可能翻譯失敗")
            raise ValueError("No Chinese characters in response")
            
    except Exception as e:
        print(f"❌ 翻譯失敗: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # 回退：保留原文
        return {'english': text, 'chinese': ''}


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
        
        print(f"📦 AI 原始回應: {result}")
        
        # 驗證必要欄位
        required_fields = ["positive_prompt", "positive_prompt_zh", "negative_prompt", "tags", "category"]
        for field in required_fields:
            if field not in result or not result[field]:
                if field == "tags":
                    result[field] = []
                elif field == "category":
                    result[field] = "Other"
                else:
                    result[field] = ""
        
        # 確保 tags 是陣列
        if not isinstance(result["tags"], list):
            result["tags"] = []
        
        # 🔥 關鍵修復：如果沒有中文翻譯，自動生成
        if not result.get("positive_prompt_zh") or result["positive_prompt_zh"] == "":
            print("⚠️ AI 未回傳中文翻譯，自動生成中文翻譯")
            try:
                translation = translate_prompt(result["positive_prompt"])
                result["positive_prompt_zh"] = translation.get("chinese", "")
            except Exception as e:
                print(f"❌ 自動翻譯失敗: {e}")
                result["positive_prompt_zh"] = "（翻譯生成失敗）"
        
        # 🔥 關鍵修復：檢查 tags 是否包含中文，若無則補充
        if result["tags"]:
            has_chinese = any(re.search(r'[\u4e00-\u9fff]', tag) for tag in result["tags"])
            if not has_chinese:
                print("⚠️ Tags 缺少中文，嘗試補充")
                try:
                    tags_with_cat = extract_tags_from_text(result["positive_prompt"])
                    zh_tags = [t for t in tags_with_cat[0] if re.search(r'[\u4e00-\u9fff]', t)]
                    result["tags"].extend(zh_tags[:5])  # 加入最多 5 個中文 tags
                except Exception as e:
                    print(f"❌ Tags 補充失敗: {e}")
        
        print(f"✅ AI 分析完成: {image_path}")
        print(f"   - 中文翻譯: {result['positive_prompt_zh'][:50]}...")
        print(f"   - Tags: {result['tags']}")
        print(f"   - 分類: {result.get('category', 'Other')}")
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


def search_images_with_gemini(query: str, images_data: list) -> list[int]:
    """
    使用 Gemini 進行智慧語意搜尋
    
    Args:
        query: 搜尋語句
        images_data: 包含 id, positive_prompt, positive_prompt_zh, tags 的圖片列表
    
    Returns:
        符合條件的 image_id 列表，依關聯性排序
    """
    try:
        if not images_data:
            return []

        # 準備候選資料（簡化內容以節省 token）
        candidates = []
        for img in images_data:
            # 組合關鍵資訊
            info = f"ID: {img['id']}\nPrompt: {img.get('positive_prompt', '')}\nChinese: {img.get('positive_prompt_zh', '')}\nTags: {', '.join(img.get('tags', []))}"
            candidates.append(info)
        
        candidates_text = "\n---\n".join(candidates)
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        search_prompt = f"""You are an intelligent search engine for an AI image database.

User Query: "{query}"

Task: Search through the following Image Items and find the ones that semantically match the User Query.
- Understand synonyms, concepts, and styles (e.g., "sad robot" matches "lonely android").
- Analyze both English and Chinese prompts.
- ranking them by relevance.

Database Items:
---
{candidates_text}
---

Return strict JSON format:
{{
    "matched_ids": [id1, id2, id3]
}}
If no matches found, return "matched_ids": []
IMPORTANT: Return ONLY valid JSON."""

        response = model.generate_content(search_prompt)
        text = response.text.strip()
        
        # 清理 JSON
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        result = json.loads(text.strip())
        return result.get("matched_ids", [])
        
    except Exception as e:
        print(f"❌ AI 搜尋失敗: {e}")
        return []

if __name__ == "__main__":
    # 測試分析功能（需要實際圖片檔案）
    import sys
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        result = analyze_image(test_image)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法: python ai_engine.py <圖片路徑>")
