import os
import sys
import unittest
import json
from unittest.mock import patch
from fastapi.testclient import TestClient

# 將專案根目錄加入路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, insert_image, DB_NAME
# Patch DB_NAME before importing app to ensure it uses the test DB if init_db is called at module level (it is in app.py line 46)
# However, app.py calls init_db() at module level. effective patching needs to happen before import or we accept init_db runs on real DB once.
# But since we want to test with a test DB, we should be careful.
# app.py calls init_db() on import. This risks creating 'bananadb.db' if it doesn't exist.
# To avoid this, we can mock init_db in app.py during import, or just let it happen (it's safe if DB exists).
# Key is that *requests* should use test DB.

TEST_DB_NAME = "test_bananadb_api.db"

# Patch database.DB_NAME globally for the test execution
with patch('database.DB_NAME', TEST_DB_NAME):
    from app import app

class TestAPI(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.patcher = patch('database.DB_NAME', TEST_DB_NAME)
        cls.patcher.start()
        
    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)

    def setUp(self):
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
        init_db()
        
        # 插入測試數據
        self.img_id = insert_image(
            filename="api_test.jpg",
            positive_prompt="api test",
            positive_prompt_zh="API 測試",
            negative_prompt="nsfw",
            tags=["api"]
        )

    def test_get_images(self):
        response = self.client.get("/api/images")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['id'], self.img_id)

    def test_favorite_flow(self):
        # 1. 初始狀態：未收藏
        response = self.client.get("/api/images/favorited")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['data']), 0)
        
        # 2. 加入收藏
        response = self.client.post(f"/api/images/{self.img_id}/favorite")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(response.json()['is_favorited'])
        self.assertIn("已加入收藏", response.json()['message'])
        
        # 3. 驗證收藏列表
        response = self.client.get("/api/images/favorited")
        self.assertEqual(len(response.json()['data']), 1)
        self.assertEqual(response.json()['data'][0]['id'], self.img_id)
        
        # 4. 再次點擊 (取消收藏)
        response = self.client.post(f"/api/images/{self.img_id}/favorite")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_favorited'])
        self.assertIn("已移除收藏", response.json()['message'])
        
        # 5. 驗證收藏列表為空
        response = self.client.get("/api/images/favorited")
        self.assertEqual(len(response.json()['data']), 0)

if __name__ == '__main__':
    unittest.main()
