"""
BananaDB FastAPI 後端主程式
提供圖片收集、上傳、查詢 API
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import requests

from database import (init_db, insert_image, get_all_images, delete_image, 
                      delete_images_batch, get_categories_stats, get_images_by_category,
                      toggle_favorite, get_favorited_images, get_favorites_count)
from ai_engine import analyze_image, search_images_with_gemini, extract_tags_from_text


# 初始化 FastAPI 應用程式
app = FastAPI(
    title="BananaDB API",
    description="本地 AI 圖片資料庫與提示詞逆向工程系統",
    version="1.0.0"
)

# 設定 CORS（允許 Chrome 擴充功能存取）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "chrome-extension://*", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 建立上傳資料夾
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 建立模板資料夾
TEMPLATE_DIR = Path("templates")
TEMPLATE_DIR.mkdir(exist_ok=True)

# 初始化資料庫
init_db()


# ============ Pydantic 模型定義 ============

class CollectURLRequest(BaseModel):
    """URL 收集請求模型"""
    image_url: str
    page_url: str
    context_text: Optional[str] = ""
    skip_ai: Optional[bool] = False


class APIResponse(BaseModel):
    """標準 API 回應模型"""
    success: bool
    message: str
    data: Optional[dict] = None


# ============ API 端點 ============

@app.get("/")
async def serve_index():
    """提供前端 HTML 頁面"""
    index_path = TEMPLATE_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse(
        status_code=404,
        content={"error": "前端頁面不存在，請先建立 templates/index.html"}
    )


@app.post("/api/collect_url")
async def collect_url(request: CollectURLRequest):
    """
    從 URL 收集圖片並分析
    
    接收來自 Chrome 擴充功能的圖片 URL，下載後進行 AI 分析並儲存
    """
    try:
        # 1. 下載圖片（設定 User-Agent 與 Referer 以繞過基本反爬蟲機制）
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': request.page_url,
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
        }
        
        print(f"📥 正在下載圖片: {request.image_url}")
        response = requests.get(request.image_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 2. 儲存圖片（使用 UUID 命名避免衝突）
        file_extension = request.image_url.split('.')[-1].split('?')[0]
        if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            file_extension = 'jpg'
        
        filename = f"{uuid.uuid4()}.{file_extension}"
        filepath = UPLOAD_DIR / filename
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"💾 圖片已儲存: {filepath}")
        
        # 3. AI 分析或使用提供的 prompt
        if request.skip_ai and request.context_text:
            # 使用者提供的 prompt，跳過 AI 分析但自動翻譯並提取 tags
            print("\n" + "="*60)
            print("⚡ 跳過 AI 分析，使用提供的 prompt 並自動翻譯 + 提取 tags + 判斷分類")
            print(f"📝 原始 Prompt 長度: {len(request.context_text)} 字元")
            print(f"📝 Prompt 預覽: {request.context_text[:100]}...")
            print("="*60 + "\n")
            
            from ai_engine import translate_prompt
            
            # 翻譯
            print("🔄 開始翻譯...")
            translation = translate_prompt(request.context_text)
            print(f"✅ 翻譯結果:")
            print(f"   - English: {translation.get('english', '')[:80]}...")
            print(f"   - Chinese: {translation.get('chinese', '')[:80]}...")
            
            # 提取 tags 與 category
            print("\n🏷️ 開始提取 tags...")
            tags, category = extract_tags_from_text(request.context_text)
            print(f"✅ Tags 提取結果: {tags}")
            print(f"✅ 分類: {category}")
            
            analysis_result = {
                'positive_prompt': translation['english'] or request.context_text,
                'positive_prompt_zh': translation['chinese'],
                'negative_prompt': 'low quality, blurry',
                'tags': tags,
                'category': category
            }
            
            print("\n📦 最終 analysis_result:")
            print(f"   - positive_prompt: {analysis_result['positive_prompt'][:80]}...")
            print(f"   - positive_prompt_zh: {analysis_result['positive_prompt_zh'][:80]}...")
            print(f"   - tags: {analysis_result['tags']}")
            print(f"   - category: {analysis_result['category']}")
            print("="*60 + "\n")
        else:
            # 正常 AI 分析
            analysis_result = analyze_image(str(filepath), request.context_text)
        
        # 4. 儲存至資料庫
        image_id = insert_image(
            filename=filename,
            positive_prompt=analysis_result['positive_prompt'],
            positive_prompt_zh=analysis_result.get('positive_prompt_zh', ''),
            negative_prompt=analysis_result.get('negative_prompt', ''),
            tags=analysis_result.get('tags', []),
            source_url=request.image_url,
            category=analysis_result.get('category', 'Other')
        )
        
        return JSONResponse(content={
            "success": True,
            "message": "圖片收集成功",
            "data": {
                "image_id": image_id,
                "filename": filename,
                "analysis": analysis_result
            }
        })
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 圖片下載失敗: {e}")
        raise HTTPException(status_code=400, detail=f"圖片下載失敗: {str(e)}")
    
    except Exception as e:
        print(f"❌ 處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"處理失敗: {str(e)}")


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    上傳本地圖片並分析
    
    接收使用者上傳的圖片檔案，進行 AI 分析並儲存
    """
    try:
        # 1. 驗證檔案類型
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="不支援的檔案類型，請上傳圖片檔案")
        
        # 2. 儲存圖片
        file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{file_extension}"
        filepath = UPLOAD_DIR / filename
        
        with open(filepath, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"💾 圖片已上傳: {filepath}")
        
        # 3. AI 分析
        analysis_result = analyze_image(str(filepath))
        
        # 4. 寫入資料庫
        image_id = insert_image(
            filename=filename,
            positive_prompt=analysis_result['positive_prompt'],
            positive_prompt_zh=analysis_result['positive_prompt_zh'],
            negative_prompt=analysis_result['negative_prompt'],
            tags=analysis_result['tags'],
            source_url=None  # 本地上傳無來源 URL
        )
        
        return JSONResponse(content={
            "success": True,
            "message": "圖片上傳成功",
            "data": {
                "image_id": image_id,
                "filename": filename,
                "analysis": analysis_result
            }
        })
        
    except Exception as e:
        print(f"❌ 上傳失敗: {e}")
        raise HTTPException(status_code=500, detail=f"上傳失敗: {str(e)}")


@app.get("/api/images")
async def list_images(category: Optional[str] = None):
    """
    取得所有圖片資料，或根據分類篩選
    
    Args:
        category: 選填，分類名稱（例如 "Portrait", "Landscape"）
    """
    try:
        if category:
            if category == 'favorites':
                images = get_favorited_images()
            else:
                images = get_images_by_category(category)
        else:
            images = get_all_images()
        
        return JSONResponse(content={
            "success": True,
            "count": len(images),
            "data": images
        })
    except Exception as e:
        print(f"❌ 查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


class DeleteImagesRequest(BaseModel):
    """批次刪除請求模型"""
    image_ids: list[int]


@app.delete("/api/images/{image_id}")
async def delete_single_image(image_id: int):
    """
    刪除單筆圖片
    
    依據圖片 ID 刪除記錄與檔案
    """
    try:
        success = delete_image(image_id)
        if not success:
            raise HTTPException(status_code=404, detail="圖片不存在")
        
        return JSONResponse(content={
            "success": True,
            "message": f"成功刪除圖片 ID: {image_id}"
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 刪除失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除失敗: {str(e)}")


@app.post("/api/images/delete_batch")
async def delete_multiple_images(request: DeleteImagesRequest):
    """
    批次刪除多筆圖片
    
    接收圖片 ID 陣列，批次刪除記錄與檔案
    """
    try:
        deleted_count = delete_images_batch(request.image_ids)
        
        return JSONResponse(content={
            "success": True,
            "message": f"成功刪除 {deleted_count} 張圖片",
            "data": {"deleted_count": deleted_count}
        })
    except Exception as e:
        print(f"❌ 批次刪除失敗: {e}")
        raise HTTPException(status_code=500, detail=f"批次刪除失敗: {str(e)}")


@app.get("/api/search")
async def search_images(q: str):
    """
    AI 智慧搜尋
    
    Args:
        q: 搜尋關鍵字
    """
    try:
        print(f"🔍 AI 搜尋啟動: {q}")
        
        # 1. 取得所有圖片資料
        all_images = get_all_images()
        
        if not all_images:
            return JSONResponse(content={"success": True, "count": 0, "data": []})
            
        # 2. 呼叫 Gemini 進行語意搜尋
        matched_ids = search_images_with_gemini(q, all_images)
        print(f"✅ 搜尋結果 ID: {matched_ids}")
        
        # 3. 過濾並排序結果（保持 AI 回傳的順序）
        # 建立 ID 到圖片的映射以便快速查找
        img_map = {img['id']: img for img in all_images}
        
        results = []
        for mid in matched_ids:
            if mid in img_map:
                results.append(img_map[mid])
                
        return JSONResponse(content={
            "success": True,
            "count": len(results),
            "data": results
        })
        
    except Exception as e:
        print(f"❌ 搜尋失敗: {e}")
        raise HTTPException(status_code=500, detail=f"搜尋失敗: {str(e)}")


@app.get("/api/categories")
async def get_categories():
    """
    取得所有分類與統計資料
    """
    try:
        stats = get_categories_stats()
        
        # 預設分類列表（中英雙語與顏色）
        default_categories = [
            {"id": "Portrait", "label": "人像", "color": "bg-blue-600"},
            {"id": "Landscape", "label": "風景", "color": "bg-green-600"},
            {"id": "Animal", "label": "動物", "color": "bg-yellow-600"},
            {"id": "Architecture", "label": "建築", "color": "bg-gray-600"},
            {"id": "Sci-Fi", "label": "科幻", "color": "bg-purple-600"},
            {"id": "Art", "label": "藝術", "color": "bg-pink-600"},
            {"id": "Food", "label": "食物", "color": "bg-orange-600"},
            {"id": "Fashion", "label": "時尚", "color": "bg-red-600"},
            {"id": "Other", "label": "其他", "color": "bg-gray-500"}
        ]
        
        # 加入計數
        for cat in default_categories:
            cat["count"] = stats.get(cat["id"], 0)

        # 🚀 插入「收藏」分類到第一位 (或最前面)
        favorites_count = get_favorites_count()
        if favorites_count > 0:
            default_categories.insert(0, {
                "id": "favorites", 
                "label": "⭐ 收藏", 
                "color": "bg-yellow-500",
                "count": favorites_count
            })
        
        return JSONResponse(content={
            "success": True,
            "data": default_categories
        })
    except Exception as e:
        print(f"❌ 分類查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分類查詢失敗: {str(e)}")


@app.post("/api/images/{image_id}/favorite")
async def toggle_image_favorite(image_id: int):
    """
    切換圖片的收藏狀態
    
    Args:
        image_id: 圖片 ID
    
    Returns:
        新的收藏狀態
    """
    try:
        new_status = toggle_favorite(image_id)
        
        return JSONResponse(content={
            "success": True,
            "is_favorited": new_status,
            "message": f"圖片已{'加入' if new_status else '移除'}收藏"
        })
    except Exception as e:
        print(f"❌ 收藏操作失敗: {e}")
        raise HTTPException(status_code=500, detail=f"收藏操作失敗: {str(e)}")


@app.get("/api/images/favorited")
async def list_favorited_images():
    """
    取得所有已收藏的圖片
    
    Returns:
        收藏圖片列表
    """
    try:
        images = get_favorited_images()
        
        return JSONResponse(content={
            "success": True,
            "count": len(images),
            "data": images
        })
    except Exception as e:
        print(f"❌ 收藏查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"收藏查詢失敗: {str(e)}")


# 掛載靜態檔案（圖片存取）
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ============ 啟動資訊 ============

@app.on_event("startup")
async def startup_event():
    """應用程式啟動時的訊息"""
    print("=" * 60)
    print("🍌 BananaDB 伺服器已啟動")
    print("=" * 60)
    print(f"📂 圖片儲存路徑: {UPLOAD_DIR.absolute()}")
    print(f"🌐 API 文件: http://localhost:8000/docs")
    print(f"🎨 前端頁面: http://localhost:8000/")
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
