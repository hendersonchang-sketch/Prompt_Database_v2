"""測試 Gemini Vision API"""
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

print("=== Testing Gemini Vision API ===\n")

# 測試 1: 列出可用模型
print("1. Available models:")
try:
    models = list(genai.list_models())
    vision_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
    for m in vision_models[:5]:
        print(f"   - {m.name}")
    print()
except Exception as e:
    print(f"   Error: {e}\n")

# 測試 2: 測試圖片分析
print("2. Testing image analysis:")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    image_path = 'uploads/36667f24-8e95-40ed-812a-4f615a3040ba.png'
    
    print(f"   Loading image: {image_path}")
    image = Image.open(image_path)
    print(f"   Image size: {image.size}")
    print(f"   Image format: {image.format}")
    
    print("   Calling Gemini API...")
    response = model.generate_content([
        "Describe this image in one sentence.",
        image
    ])
    
    print(f"   Success! Response: {response.text[:100]}...")
    
except Exception as e:
    print(f"   ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")
