"""
合并中文和日文QA数据
"""

import json
import os


def merge_qa_files():
    """合并QA文件"""
    print("=" * 60)
    print("合并中文和日文QA数据")
    print("=" * 60)
    
    # 读取中文QA
    cn_file = 'official_qa_complete.json'
    cn_qa = []
    
    if os.path.exists(cn_file):
        try:
            with open(cn_file, 'r', encoding='utf-8') as f:
                cn_qa = json.load(f)
            print(f"\n✓ 中文QA: {len(cn_qa)} 条")
        except Exception as e:
            print(f"\n❌ 读取中文QA失败: {e}")
    else:
        print(f"\n⚠ 未找到中文QA文件: {cn_file}")
    
    # 读取日文QA
    jp_file = 'official_qa_jp.json'
    jp_qa = []
    
    if os.path.exists(jp_file):
        try:
            with open(jp_file, 'r', encoding='utf-8') as f:
                jp_qa = json.load(f)
            print(f"✓ 日文QA: {len(jp_qa)} 条")
        except Exception as e:
            print(f"❌ 读取日文QA失败: {e}")
    else:
        print(f"⚠ 未找到日文QA文件: {jp_file}")
    
    # 合并
    merged_qa = cn_qa + jp_qa
    
    if merged_qa:
        # 保存合并结果
        output_file = 'official_qa_merged.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_qa, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✓ 合并完成！")
        print(f"✓ 中文QA: {len(cn_qa)} 条")
        print(f"✓ 日文QA: {len(jp_qa)} 条")
        print(f"✓ 总计: {len(merged_qa)} 条")
        print(f"✓ 已保存到: {output_file}")
        print(f"{'='*60}")
        
        # 统计语言分布
        cn_count = sum(1 for qa in merged_qa if qa.get('language') != 'ja')
        jp_count = sum(1 for qa in merged_qa if qa.get('language') == 'ja')
        
        print(f"\n语言分布:")
        print(f"  中文: {cn_count} 条")
        print(f"  日文: {jp_count} 条")
        
        # 统计来源
        sources = {}
        for qa in merged_qa:
            source = qa.get('source', '未知')
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n来源统计:")
        for source, count in sources.items():
            print(f"  {source}: {count} 条")
    else:
        print("\n❌ 没有数据可合并")


if __name__ == "__main__":
    merge_qa_files()
