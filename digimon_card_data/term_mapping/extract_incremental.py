"""
增量提取关键词
分多次运行，每次提取不同的样本，最后合并结果
"""

import json
from pathlib import Path
from extract_with_llm import LLMKeywordExtractor
from collections import defaultdict

def incremental_extract(total_samples=1000, batch_samples=200):
    """
    增量提取关键词
    
    Args:
        total_samples: 总共要提取的样本数
        batch_samples: 每批提取的样本数
    """
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent
    output_file = script_dir / "llm_keywords_incremental.json"
    
    # 加载已有结果
    all_keywords = defaultdict(set)
    if output_file.exists():
        print(f"加载已有结果: {output_file}")
        with open(output_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            for cn, jp_list in existing.items():
                all_keywords[cn].update(jp_list)
        print(f"已有 {len(all_keywords)} 个关键词")
    
    # 计算需要提取的批次
    num_batches = (total_samples + batch_samples - 1) // batch_samples
    
    print(f"\n增量提取计划:")
    print(f"  总样本数: {total_samples}")
    print(f"  每批样本: {batch_samples}")
    print(f"  总批次数: {num_batches}")
    print()
    
    try:
        from llm_config import LLM_TYPE
        llm_type = LLM_TYPE
    except ImportError:
        llm_type = "qwen"
    
    extractor = LLMKeywordExtractor(base_dir, llm_type=llm_type)
    extractor.load_chinese_cards()
    extractor.load_japanese_cards()
    
    # 收集所有样本
    print(f"收集 {total_samples} 个样本...")
    all_samples = extractor.collect_effect_samples(sample_size=total_samples)
    print(f"实际收集到 {len(all_samples)} 个样本")
    
    # 分批处理
    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_samples
        end_idx = min(start_idx + batch_samples, len(all_samples))
        batch = all_samples[start_idx:end_idx]
        
        print(f"\n处理批次 {batch_idx + 1}/{num_batches} (样本 {start_idx+1}-{end_idx})...")
        
        # 提取关键词
        keywords = extractor.extract_keywords_with_llm(batch, batch_size=10)
        
        # 合并结果
        for cn, jp_set in keywords.items():
            all_keywords[cn].update(jp_set)
        
        # 保存中间结果
        temp_result = {cn: sorted(list(jp_set)) for cn, jp_set in all_keywords.items()}
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(temp_result, f, ensure_ascii=False, indent=2)
        
        print(f"  当前总计: {len(all_keywords)} 个关键词")
        print(f"  已保存到: {output_file}")
    
    print(f"\n增量提取完成！")
    print(f"总共提取到 {len(all_keywords)} 个关键词")
    print(f"结果保存在: {output_file}")
    
    # 生成报告
    extractor.generate_report(all_keywords, script_dir / "llm_keywords_incremental_report.md")
    
    return all_keywords


if __name__ == "__main__":
    # 配置：总共提取1000个样本，每批200个
    incremental_extract(total_samples=1000, batch_samples=200)
