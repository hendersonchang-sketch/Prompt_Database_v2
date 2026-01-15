import os
import sys

# 1. 在導入任何專案模組前設定環境變數
TEST_DB_NAME = "test_bananadb_api_env.db"
os.environ["BANANADB_DB_NAME"] = TEST_DB_NAME
if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = "dummy_key_for_testing"

# 將專案根目錄加入路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock ai_engine to avoid import issues with google.generativeai during tests
from unittest.mock import MagicMock
sys.modules["ai_engine"] = MagicMock()

from app import app
from database import init_db, insert_image
from fastapi.testclient import TestClient

def run_tests():
    print(f"🚀 開始執行 API 測試 (DB: {TEST_DB_NAME})...")
    
    # 清理舊測試資料庫
    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)
        
    try:
        # 初始化資料庫
        init_db()
        
        # 插入測試圖片
        print("📝 準備測試數據...")
        img_id = insert_image(
            filename="api_test.jpg",
            positive_prompt="api test",
            positive_prompt_zh="API 測試",
            negative_prompt="nsfw",
            tags=["api"]
        )
        
        # 使用 TestClient
        client = TestClient(app)
        
        # 1. 測試 GET /api/images
        print("🧪 測試 GET /api/images...")
        response = client.get("/api/images")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == img_id
        print("✅ GET /api/images 通過")

        # 2. 測試收藏功能
        print("🧪 測試收藏功能流程...")
        
        # 初始檢查
        response = client.get("/api/images/favorited")
        assert len(response.json()['data']) == 0
        
        # 加入收藏
        print("   - 加入收藏...")
        response = client.post(f"/api/images/{img_id}/favorite")
        assert response.status_code == 200
        assert response.json()['success'] == True
        assert response.json()['is_favorited'] == True
        
        # 驗證收藏列表
        print("   - 驗證收藏列表...")
        response = client.get("/api/images/favorited")
        assert len(response.json()['data']) == 1
        assert response.json()['data'][0]['id'] == img_id
        
        # 取消收藏
        print("   - 取消收藏...")
        response = client.post(f"/api/images/{img_id}/favorite")
        assert response.status_code == 200
        assert response.json()['is_favorited'] == False
        
        # 驗證收藏列表為空
        response = client.get("/api/images/favorited")
        assert len(response.json()['data']) == 0
        print("✅ 收藏流程測試通過")
        
        print("\n🎉 所有 API 測試通過！")
        
    finally:
        # 清理
        if os.path.exists(TEST_DB_NAME):
            try:
                os.remove(TEST_DB_NAME)
            except:
                pass

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        exit(1)
