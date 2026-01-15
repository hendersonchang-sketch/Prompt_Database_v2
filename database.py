"""
BananaDB 資料庫模組
負責 SQLite 資料庫的初始化、CRUD 操作
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


DB_NAME = "bananadb.db"


def init_db() -> None:
    """初始化資料庫，建立 images 資料表"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            positive_prompt TEXT,
            positive_prompt_zh TEXT,
            negative_prompt TEXT,
            tags TEXT,
            source_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ 資料庫 {DB_NAME} 初始化完成")


def insert_image(
    filename: str,
    positive_prompt: str,
    positive_prompt_zh: str,
    negative_prompt: str,
    tags: List[str],
    source_url: Optional[str] = None
) -> int:
    """
    插入新的圖片記錄
    
    Args:
        filename: 儲存的檔名（含路徑）
        positive_prompt: 英文正向提示詞
        positive_prompt_zh: 繁體中文正向提示詞
        negative_prompt: 負向提示詞
        tags: 標籤陣列
        source_url: 來源 URL（選填）
    
    Returns:
        插入記錄的 ID
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 將標籤陣列轉換為 JSON 字串
    tags_json = json.dumps(tags, ensure_ascii=False)
    
    cursor.execute("""
        INSERT INTO images (filename, positive_prompt, positive_prompt_zh, 
                          negative_prompt, tags, source_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (filename, positive_prompt, positive_prompt_zh, negative_prompt, 
          tags_json, source_url))
    
    image_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ 新增圖片記錄 ID: {image_id}")
    return image_id


def get_all_images() -> List[Dict[str, Any]]:
    """
    查詢所有圖片記錄，依建立時間倒序排列
    
    Returns:
        圖片記錄列表（字典陣列）
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # 讓結果以字典形式回傳
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, filename, positive_prompt, positive_prompt_zh,
               negative_prompt, tags, source_url, created_at
        FROM images
        ORDER BY created_at DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    # 轉換為字典列表，並解析 JSON 標籤
    images = []
    for row in rows:
        image_dict = dict(row)
        # 解析標籤 JSON 字串為陣列
        try:
            image_dict['tags'] = json.loads(image_dict['tags'])
        except (json.JSONDecodeError, TypeError):
            image_dict['tags'] = []
        images.append(image_dict)
    
    return images


def get_image_by_id(image_id: int) -> Optional[Dict[str, Any]]:
    """
    根據 ID 查詢單筆圖片記錄
    
    Args:
        image_id: 圖片 ID
    
    Returns:
        圖片記錄字典，若不存在則回傳 None
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, filename, positive_prompt, positive_prompt_zh,
               negative_prompt, tags, source_url, created_at
        FROM images
        WHERE id = ?
    """, (image_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        image_dict = dict(row)
        try:
            image_dict['tags'] = json.loads(image_dict['tags'])
        except (json.JSONDecodeError, TypeError):
            image_dict['tags'] = []
        return image_dict
    return None


def delete_image(image_id: int) -> bool:
    """
    刪除單筆圖片記錄與檔案
    
    Args:
        image_id: 圖片 ID
    
    Returns:
        是否刪除成功
    """
    import os
    
    # 先查詢檔名
    image = get_image_by_id(image_id)
    if not image:
        return False
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
    conn.commit()
    conn.close()
    
    # 刪除實體檔案
    try:
        file_path = os.path.join("uploads", image['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ 已刪除檔案: {file_path}")
    except Exception as e:
        print(f"⚠️ 檔案刪除失敗: {e}")
    
    print(f"✅ 已刪除記錄 ID: {image_id}")
    return True


def delete_images_batch(image_ids: list[int]) -> int:
    """
    批次刪除多筆圖片記錄與檔案
    
    Args:
        image_ids: 圖片 ID 列表
    
    Returns:
        成功刪除的數量
    """
    import os
    
    deleted_count = 0
    for image_id in image_ids:
        if delete_image(image_id):
            deleted_count += 1
    
    print(f"✅ 批次刪除完成，共刪除 {deleted_count} 筆記錄")
    return deleted_count


if __name__ == "__main__":
    # 測試資料庫初始化
    init_db()
