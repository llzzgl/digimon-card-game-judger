"""
批量关联图片与卡牌元数据
将已下载的图片与数据库中的卡牌建立关联
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple
import hashlib
import re


class ImageMetadataLinker:
    """图片 - 元数据关联器"""
    
    def __init__(self, db_path: str = "card_data/card_metadata.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.stats = {
            "images_scanned": 0,
            "images_linked": 0,
            "images_skipped": 0,
            "errors": 0
        }
    
    def scan_images(self, images_dir: Path) -> List[Dict]:
        """扫描图片目录"""
        print(f"扫描图片目录：{images_dir}")
        
        images = []
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
        
        for img_path in image_files:
            try:
                # 从文件名提取卡牌编号
                filename = img_path.name
                card_no = self.extract_card_number(filename)
                
                if card_no:
                    # 计算图片哈希
                    with open(img_path, 'rb') as f:
                        img_hash = hashlib.md5(f.read()).hexdigest()
                    
                    # 获取文件大小
                    file_size = img_path.stat().st_size
                    
                    images.append({
                        "image_path": str(img_path),
                        "filename": filename,
                        "card_no": card_no,
                        "image_hash": img_hash,
                        "file_size": file_size
                    })
                
                self.stats["images_scanned"] += 1
                
            except Exception as e:
                print(f"  扫描失败：{e}")
                self.stats["errors"] += 1
        
        print(f"  找到 {len(images)} 张可关联图片")
        return images
    
    def extract_card_number(self, filename: str) -> str:
        """从文件名提取卡牌编号"""
        # 例：AD-01_AD1-001_12571_19729_MxZmL89JbH3_jpg~card.jpg
        # 或：EX-11CN_EX11-001_12202_19354_MAVKtf6Dcx6_png~card.jpg
        # 或：BT12-091.jpg
        
        # 尝试匹配各种格式
        patterns = [
            r'AD-01_(AD\d+-\d+)',  # AD-01 格式
            r'EX-11CN_(EX\d+-\d+)',  # EX-11CN 格式
            r'(BT\d+-\d+)',  # BT 格式
            r'(ST\d+-\d+)',  # ST 格式
            r'(LM\d+-\d+)',  # LM 格式
            r'(RB\d+-\d+)',  # RB 格式
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)
        
        # 尝试通用格式：XXX-XXX
        match = re.search(r'([A-Z]{1,3}\d+-\d+)', filename)
        if match:
            return match.group(1)
        
        return ""
    
    def link_images(self, images: List[Dict]) -> int:
        """关联图片到元数据"""
        print(f"\n开始关联 {len(images)} 张图片...")
        
        cursor = self.conn.cursor()
        linked_count = 0
        
        for img in images:
            try:
                card_no = img["card_no"]
                
                # 检查数据库中是否有这张卡牌
                cursor.execute("SELECT card_id FROM cards WHERE card_id = ?", (card_no,))
                row = cursor.fetchone()
                
                if row:
                    # 检查是否已有关联
                    cursor.execute("SELECT image_id FROM images WHERE image_path = ?", (img["image_path"],))
                    existing = cursor.fetchone()
                    
                    if not existing:
                        # 插入新关联
                        image_id = Path(img["image_path"]).stem
                        cursor.execute("""
                            INSERT OR REPLACE INTO images
                            (image_id, card_id, image_type, image_path, image_hash, file_size)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (image_id, card_no, "normal", img["image_path"], img["image_hash"], img["file_size"]))
                        
                        linked_count += 1
                        self.stats["images_linked"] += 1
                        
                        if linked_count % 500 == 0:
                            print(f"  已关联 {linked_count} 张...")
                    else:
                        self.stats["images_skipped"] += 1
                else:
                    # 卡牌不在数据库中
                    print(f"  ⚠️ 卡牌 {card_no} 不在数据库中")
                    self.stats["images_skipped"] += 1
                
            except Exception as e:
                print(f"  关联失败：{e}")
                self.stats["errors"] += 1
        
        self.conn.commit()
        return linked_count
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cards")
        card_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM images")
        image_count = cursor.fetchone()[0]
        
        return {
            "total_cards": card_count,
            "total_images": image_count,
            "link_rate": f"{(image_count/card_count*100):.1f}%" if card_count > 0 else "0%"
        }
    
    def close(self):
        """关闭数据库"""
        self.conn.close()


def main():
    """主函数"""
    print("=" * 60)
    print("DTCG 图片 - 元数据批量关联工具")
    print("=" * 60)
    print()
    
    project_root = Path(__file__).parent
    
    # 初始化关联器
    linker = ImageMetadataLinker(str(project_root / "card_data" / "card_metadata.db"))
    
    # 扫描日文图片
    jp_images_dir = project_root / "card_data" / "images" / "jp" / "raw"
    if jp_images_dir.exists():
        jp_images = linker.scan_images(jp_images_dir)
        linker.link_images(jp_images)
    else:
        print(f"⚠️ 日文图片目录不存在：{jp_images_dir}")
    
    # 扫描中文图片
    cn_images_dir = project_root / "card_data" / "images" / "cn" / "raw"
    if cn_images_dir.exists():
        cn_images = linker.scan_images(cn_images_dir)
        linker.link_images(cn_images)
    else:
        print(f"⚠️ 中文图片目录不存在：{cn_images_dir}")
    
    # 输出统计
    print()
    print("=" * 60)
    print("关联完成")
    print("=" * 60)
    print(f"扫描图片：{linker.stats['images_scanned']} 张")
    print(f"新关联：{linker.stats['images_linked']} 张")
    print(f"跳过：{linker.stats['images_skipped']} 张")
    print(f"错误：{linker.stats['errors']} 次")
    
    # 数据库统计
    stats = linker.get_stats()
    print()
    print("数据库状态:")
    print(f"  卡牌总数：{stats['total_cards']} 张")
    print(f"  图片索引：{stats['total_images']} 张")
    print(f"  关联率：{stats['link_rate']}")
    
    linker.close()
    
    return linker.stats


if __name__ == "__main__":
    stats = main()
    import sys
    sys.exit(0 if stats["images_linked"] > 0 else 1)
