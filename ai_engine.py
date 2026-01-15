"""
BananaDB AI 分析引擎
使用 Google Gemini 2.0 Flash Vision 逆向工程提示詞
"""
import os
import re
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


# System Prompt for Gemini Banana Pro Visual Logic Analysis
BANANA_PRO_SYSTEM_PROMPT = """# Role
You are a "Gemini Banana Pro" Visual Logic Specialist. Your goal is to reverse-engineer an image into a high-reasoning natural language prompt that leverages Gemini Banana Pro's specific capabilities (Text Rendering, Logical Layouts, Consistent Characters).

# Task
Analyze the provided image and generate a "Structured Instruction" prompt in natural language paragraph format.

# Analysis Framework (Internal Thought Process)

1. **Text & Information**:
   - Identify EXACT text visible in the image (Titles, Labels, Captions, Handwriting, Signs)
   - *CRUCIAL*: Banana Pro excels at rendering Chinese/English text. You MUST transcribe exact text accurately
   - Note font styles (bold, handwritten, 3D, floating text, etc.)

2. **Logical Structure**:
   - Determine the image type: Infographic, Mind Map, Flowchart, Storyboard, Comparison, Timeline, Photo Scene
   - Describe the *relationship* between elements:
     - "A flowchart showing cause and effect"
     - "A split-screen before/after comparison"
     - "A radial mind map with central node branching to 4 categories"
     - "A sequential storyboard with 3 panels"
   - Identify data flow, hierarchy, or narrative sequence

3. **Visual Style & Medium**:
   - Banana Pro-specific keywords:
     - "Hand-drawn sketch on paper"
     - "3D layered typography with depth"
     - "Cutout paper style with shadows"
     - "Photorealistic cinematic shot"
     - "Marker illustration on whiteboard"
     - "Digital flat design with gradients"
     - "Watercolor painting aesthetic"
   - Lighting and atmosphere (warm, cool, dramatic, soft)

4. **Subject Consistency** (for character/object scenes):
   - Describe distinctive features for consistency:
     - Character: clothing, accessories, hairstyle, age, expression
     - Objects: material, color, shape, brand details
   - Specify if same subject appears multiple times

5. **Composition & Camera**:
   - Layout: top-down, isometric, split-screen, grid layout, centered
   - Camera angle (if applicable): wide shot, close-up, eye-level, bird's eye view
   - Aspect ratio and framing

# Output Format - Natural Language Prompt

Generate a coherent paragraph following this flow:
1. **Context & Type**: Define the image type (e.g., "A hand-drawn mind map about...", "A cinematic movie still showing...")
2. **Content & Logic**: Describe the scene's action OR the diagram's data flow/relationships
3. **Text Specification**: Explicitly state visible text and its style (e.g., "Render the title '專案管理' in bold black marker", "Display '2024' in floating 3D white letters")
4. **Visual Style & Atmosphere**: Medium, materials, lighting, color palette
5. **Composition**: Camera angle, layout structure, perspective

# Example Prompts

**Example 1 (Mind Map):**
"Generate a hand-drawn mind map on a textured paper background. The central node contains the text '專案管理' in bold black marker style. Four branches radiate outward in different colors (red, blue, green, yellow), labeled 'Planning', 'Execution', 'Monitoring', and 'Closing'. Small doodle icons represent each phase (calendar, gear, chart, checkmark). The style should look like a professional study note with clean lines, high legibility, and warm lighting."

**Example 2 (Split-Screen Scene):**
"A split-screen comparison showing the same street corner in two seasons. Left side displays 'SUMMER' in floating white 3D letters at the top, showing sunny weather with green trees and people in t-shirts. Right side shows 'WINTER' in icy blue 3D text, depicting snow-covered streets and bare branches. Maintain the exact same perspective, building architecture, and camera angle on both sides. Photorealistic rendering with cinematic color grading."

**Example 3 (Infographic):**
"Create a vertical timeline infographic titled 'AI 發展史' at the top in bold modern sans-serif font. Five milestone nodes arranged vertically from 1956 to 2024, each with a year label in large numbers, a circular icon, and a brief description in Traditional Chinese. Connect nodes with a flowing blue gradient line. Use a clean white background with subtle shadows for depth. Professional business presentation style."

# JSON Output Structure

Based on your analysis, return the following JSON format (no markdown blocks):

{
  "positive_prompt": "[Natural language paragraph following the flow above - in English, 50-150 words]",
  "positive_prompt_zh": "[完整的繁體中文翻譯段落，必須包含所有細節與文字指令]",
  "negative_prompt": "low quality, blurry, distorted, pixelated, watermark, signature, out of focus, amateur, messy layout, illegible text",
  "tags": ["keyword1", "關鍵字1", "keyword2", "關鍵字2", ...],
  "category": "Art"
}

# Available Categories
- Portrait (人像/肖像) - people photos, portraits
- Landscape (風景) - nature, scenery, cityscapes
- Animal (動物) - pets, wildlife
- Architecture (建築) - buildings, interiors
- Sci-Fi (科幻) - futuristic, robots, space
- Art (藝術/插畫) - illustrations, diagrams, infographics, mind maps
- Food (食物) - cuisine, dishes
- Fashion (時尚) - clothing, accessories
- Other (其他) - anything else

# CRITICAL VALIDATION
- positive_prompt MUST be a natural paragraph (not comma-separated keywords)
- If any text is visible in the image, you MUST transcribe it in the prompt
- positive_prompt_zh MUST be a COMPLETE Traditional Chinese translation of positive_prompt (MANDATORY, cannot be empty)
- tags MUST include BOTH English and Traditional Chinese tags in the SAME array (e.g., ["embroidery", "刺繡", "bird", "鳥", "flower", "花"])
- IMPORTANT: At least 40% of tags must be in Traditional Chinese characters
- tags should have 6-10 items total (mixed English and Chinese)
- category MUST match one of the predefined options
- Focus on LOGICAL STRUCTURE for diagrams/charts, NARRATIVE FLOW for scenes
- Response MUST be ONLY valid JSON (no ```json markdown)"""


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
        words = re.findall(r'\b\w{3,}\b', text[:200])
        return (words[:5] if words else ["未分類", "uncategorized"], "Other")


def translate_prompt(text: str) -> Dict[str, str]:
    """
    使用 Gemini 翻譯 prompt（無長度限制）
    
    Args:
        text: 要翻譯的文字
    
    Returns:
        包含 'english' 和 'chinese' 的字典
    """
    # 如果已經是中文，直接返回
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    if has_chinese:
        print("➡️ 偵測到中文，保留原文")
        return {'english': '', 'chinese': text}
    
    print(f"🔄 開始翻譯 ({len(text)} 字元)")
    
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # 明確要求完整翻譯
        prompt = f"""Translate the following AI image prompt into Traditional Chinese (Taiwan).

REQUIREMENTS:
1. Translate the ENTIRE text completely and accurately
2. Use Traditional Chinese characters (繁體中文)
3. Maintain all technical terms and details
4. Do NOT summarize or shorten the translation
5. Output ONLY the Traditional Chinese translation (no English, no explanations, no markdown)

Text to translate:
{text}

IMPORTANT: Provide a COMPLETE translation of ALL the content above."""

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
