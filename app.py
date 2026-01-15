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

from database import init_db, insert_image, get_all_images, delete_image, delete_images_batch
from ai_engine import analyze_image


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
            # 使用者提供的 prompt，跳過 AI 分析但自動翻譯
            print("⚡ 跳過 AI 分析，使用提供的 prompt 並自動翻譯")
            from ai_engine import translate_prompt
            
            translation = translate_prompt(request.context_text)
            
            analysis_result = {
                'positive_prompt': translation['english'] or request.context_text,
                'positive_prompt_zh': translation['chinese'],
                'negative_prompt': 'low quality, blurry',
                'tags': []
            }
        else:
            # 正常 AI 分析
            analysis_result = analyze_image(str(filepath), request.context_text)
        
        # 4. 寫入資料庫
        image_id = insert_image(
            filename=filename,
            positive_prompt=analysis_result['positive_prompt'],
            positive_prompt_zh=analysis_result['positive_prompt_zh'],
            negative_prompt=analysis_result['negative_prompt'],
            tags=analysis_result['tags'],
            source_url=request.page_url
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
async def get_images():
    """
    查詢所有圖片
    
    回傳資料庫中的所有圖片記錄，依建立時間倒序排列
    """
    try:
        images = get_all_images()
        return JSONResponse(content={
            "success": True,
            "message": f"成功查詢 {len(images)} 張圖片",
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
