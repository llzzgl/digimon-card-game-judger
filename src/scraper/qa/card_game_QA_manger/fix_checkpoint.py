"""
修复检查点文件
"""
import json
from pathlib import Path


def fix_checkpoint():
    """修复或清理检查点文件"""
    print("="*60)
    print("检查点修复工具")
    print("="*60)
    
    base_dir = Path(__file__).parent
    checkpoint_files = list(base_dir.glob("official_qa_cn_*_checkpoint.json"))
    
    if not checkpoint_files:
        print("\n未找到检查点文件")
        return
    
    print(f"\n找到 {len(checkpoint_files)} 个检查点文件:")
    for i, f in enumerate(checkpoint_files, 1):
        print(f"  {i}. {f.name}")
        
        # 读取检查点信息
        try:
            with open(f, 'r', encoding='utf-8') as file:
                checkpoint = json.load(file)
                last_index = checkpoint.get('last_index', -1)
                total = checkpoint.get('total', 0)
                translated = checkpoint.get('translated', [])
                
                print(f"     last_index: {last_index}")
                print(f"     total: {total}")
                print(f"     已翻译: {len(translated)} 条")
        except Exception as e:
            print(f"     ✗ 读取失败: {e}")
    
    print("\n选项:")
    print("  1. 删除所有检查点（重新开始）")
    print("  2. 查看检查点详情")
    print("  3. 退出")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        confirm = input("确认删除所有检查点? (y/n): ").strip().lower()
        if confirm == 'y':
            for f in checkpoint_files:
                f.unlink()
                print(f"✓ 已删除: {f.name}")
            print("\n✓ 所有检查点已清除，可以重新开始翻译")
    
    elif choice == "2":
        for f in checkpoint_files:
            print(f"\n{'='*60}")
            print(f"文件: {f.name}")
            print('='*60)
            
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    checkpoint = json.load(file)
                    
                print(f"last_index: {checkpoint.get('last_index', -1)}")
                print(f"total: {checkpoint.get('total', 0)}")
                
                translated = checkpoint.get('translated', [])
                print(f"已翻译: {len(translated)} 条")
                
                if translated:
                    print("\n前3条翻译:")
                    for i, qa in enumerate(translated[:3], 1):
                        print(f"\n  {i}. QA#{qa.get('qa_number', 'N/A')}")
                        print(f"     问题: {qa.get('question', '')[:50]}...")
                        print(f"     答案: {qa.get('answer', '')[:50]}...")
            except Exception as e:
                print(f"✗ 读取失败: {e}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    fix_checkpoint()
