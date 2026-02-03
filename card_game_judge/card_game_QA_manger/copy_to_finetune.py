"""
将爬取的QA数据复制到微调数据目录
"""
import shutil
import os
from pathlib import Path


def copy_qa_to_finetune():
    """复制QA数据到微调目录"""
    
    # 源文件
    source_file = Path(__file__).parent / "official_qa.json"
    
    # 目标目录和文件
    target_dir = Path(__file__).parent.parent / "finetune" / "origin_data"
    target_file = target_dir / "official_qa.json"
    
    # 检查源文件是否存在
    if not source_file.exists():
        print(f"❌ 源文件不存在: {source_file}")
        print("   请先运行 scraper_faq.py 爬取数据")
        return False
    
    # 创建目标目录（如果不存在）
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制文件
    try:
        shutil.copy2(source_file, target_file)
        print(f"✅ 成功复制QA数据")
        print(f"   源: {source_file}")
        print(f"   目标: {target_file}")
        
        # 显示文件大小
        size = os.path.getsize(target_file)
        print(f"   大小: {size:,} 字节")
        
        return True
    except Exception as e:
        print(f"❌ 复制失败: {e}")
        return False


def main():
    print("=" * 60)
    print("复制QA数据到微调目录")
    print("=" * 60)
    
    if copy_qa_to_finetune():
        print("\n" + "=" * 60)
        print("✅ 完成！")
        print("=" * 60)
        print("\n下一步:")
        print("  cd ../finetune")
        print("  python collect_all_data.py")
    else:
        print("\n" + "=" * 60)
        print("❌ 失败")
        print("=" * 60)


if __name__ == "__main__":
    main()
