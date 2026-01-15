import os
import sys
import unittest
import sqlite3
import json
from unittest.mock import patch

# 將專案根目錄加入路徑以便導入模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, toggle_favorite, get_favorited_images, insert_image, DB_NAME

TEST_DB_NAME = "test_bananadb.db"

class TestDatabase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # 覆蓋資料庫名稱為測試資料庫
        cls.patcher = patch('database.DB_NAME', TEST_DB_NAME)
        cls.patcher.start()
        
    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()
        # 清理測試資料庫
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)

    def setUp(self):
        # 每個測試前初始化資料庫
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
        init_db()

    def test_toggle_favorite(self):
        # 1. 插入測試圖片
        image_id = insert_image(
            filename="test.jpg",
            positive_prompt="test prompt",
            positive_prompt_zh="測試提示詞",
            negative_prompt="low quality",
            tags=["tag1", "tag2"]
        )
        
        # 2. 測試初始狀態 (False)
        conn = sqlite3.connect(TEST_DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT is_favorited FROM images WHERE id = ?", (image_id,))
        self.assertFalse(bool(cursor.fetchone()[0]))
        conn.close()
        
        # 3. 測試切換為收藏 (True)
        result = toggle_favorite(image_id)
        self.assertTrue(result)
        
        # 驗證資料庫
        conn = sqlite3.connect(TEST_DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT is_favorited FROM images WHERE id = ?", (image_id,))
        self.assertTrue(bool(cursor.fetchone()[0]))
        conn.close()
        
        # 4. 測試再次切換取消收藏 (False)
        result = toggle_favorite(image_id)
        self.assertFalse(result)

    def test_get_favorited_images(self):
        # 1. 插入兩張圖片
        id1 = insert_image("img1.jpg", "p1", "z1", "n1", ["t1"])
        id2 = insert_image("img2.jpg", "p2", "z2", "n2", ["t2"])
        
        # 2. 收藏其中一張
        toggle_favorite(id1)
        
        # 3. 獲取收藏列表
        images = get_favorited_images()
        
        # 驗證
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]['id'], id1)
        self.assertEqual(images[0]['filename'], "img1.jpg")
        self.assertTrue(images[0]['is_favorited'])

if __name__ == '__main__':
    unittest.main()
