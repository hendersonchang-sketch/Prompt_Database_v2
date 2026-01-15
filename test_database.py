"""
BananaDB 資料庫測試腳本
驗證資料庫初始化與基本操作功能
"""
from database import init_db, insert_image, get_all_images, get_image_by_id

def test_database():
    """測試資料庫基本功能"""
    print("=" * 60)
    print("🧪 開始測試 BananaDB 資料庫")
    print("=" * 60)
    
    # 1. 測試資料庫初始化
    print("\n1️⃣ 測試資料庫初始化...")
    init_db()
    
    # 2. 測試插入記錄
    print("\n2️⃣ 測試插入測試記錄...")
    test_id = insert_image(
        filename="test_image_001.jpg",
        positive_prompt="A beautiful sunset over mountains, dramatic lighting, 8K resolution",
        positive_prompt_zh="山巒上的美麗日落，戲劇性光線，8K 解析度",
        negative_prompt="low quality, blurry, distorted",
        tags=["sunset", "mountains", "landscape", "dramatic"],
        source_url="https://example.com/test"
    )
    print(f"✅ 成功插入記錄，ID: {test_id}")
    
    # 3. 測試查詢單筆記錄
    print("\n3️⃣ 測試查詢單筆記錄...")
    image = get_image_by_id(test_id)
    if image:
        print(f"✅ 查詢成功:")
        print(f"   檔名: {image['filename']}")
        print(f"   英文提示詞: {image['positive_prompt'][:50]}...")
        print(f"   中文提示詞: {image['positive_prompt_zh']}")
        print(f"   標籤: {', '.join(image['tags'])}")
    else:
        print("❌ 查詢失敗")
    
    # 4. 測試查詢所有記錄
    print("\n4️⃣ 測試查詢所有記錄...")
    all_images = get_all_images()
    print(f"✅ 共查詢到 {len(all_images)} 筆記錄")
    
    for img in all_images[:3]:  # 只顯示前 3 筆
        print(f"   - ID {img['id']}: {img['filename']}")
    
    print("\n" + "=" * 60)
    print("✅ 資料庫測試完成")
    print("=" * 60)

if __name__ == "__main__":
    test_database()
