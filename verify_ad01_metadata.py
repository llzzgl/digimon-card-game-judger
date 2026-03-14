"""验证 AD-01 卡牌元数据"""
import sqlite3
from pathlib import Path

project_root = Path(__file__).parent
db_path = project_root / "card_data" / "card_metadata.db"

conn = sqlite3.connect(str(db_path))
c = conn.cursor()

print("=" * 60)
print("AD-01 卡牌元数据验证")
print("=" * 60)

# 查询 AD-01 卡牌
c.execute("SELECT card_id, card_name, pack, rarity FROM cards WHERE card_id LIKE 'AD1%' ORDER BY card_id")
ad01_cards = c.fetchall()
print(f"\n数据库中 AD-01 卡牌数量：{len(ad01_cards)}")
print("\n卡牌列表:")
for row in ad01_cards:
    print(f"  {row[0]} - {row[1]} ({row[3]})")

# 查询 AD-01 图片关联
c.execute("""
    SELECT i.card_id, i.image_path 
    FROM images i 
    WHERE i.card_id LIKE 'AD1%' 
    ORDER BY i.card_id
""")
ad01_images = c.fetchall()
print(f"\nAD-01 图片关联数量：{len(ad01_images)}")
print("\n图片关联:")
for row in ad01_images:
    print(f"  {row[0]} -> {Path(row[1]).name}")

# 统计
print("\n" + "=" * 60)
print("统计摘要")
print("=" * 60)
c.execute("SELECT COUNT(*) FROM cards")
total_cards = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM images")
total_images = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM images WHERE card_id LIKE 'AD1%'")
ad01_image_count = c.fetchone()[0]

print(f"总卡牌数：{total_cards}")
print(f"总图片数：{total_images}")
print(f"AD-01 图片关联数：{ad01_image_count}")

conn.close()
