#!/usr/bin/env python3
import sys
sys.path.insert(0, 'D:\\LLMProject\\dtcg_judger')
sys.stdout.reconfigure(encoding='utf-8')

from skill.src.judger import DTCGJudger

judger = DTCGJudger()

print("=== 调试搜索流程 ===\n")

# 测试"亚古"
query = "亚古"
print(f"查询：'{query}'")

# 1. 检查别名映射
if query.lower() in judger.name_variants:
    standard = judger.name_variants[query.lower()]
    print(f"  别名映射：'{query}' → '{standard}'")
    
    # 2. 检查日文映射
    if standard in judger.cn_to_jp_map:
        jp_name = judger.cn_to_jp_map[standard]
        print(f"  日文映射：'{standard}' → '{jp_name}'")
        
        # 3. 检查关键词
        keywords = judger._extract_keywords(jp_name.lower())
        print(f"  日文关键词：{keywords[:10]}")
        
        # 4. 检查索引
        for kw in keywords[:5]:
            if kw in judger.card_name_index:
                print(f"  关键词 '{kw}' 在索引中，有 {len(judger.card_name_index[kw])} 张卡牌")

# 实际搜索
print(f"\n实际搜索结果:")
results = judger.search_card_by_name(query, language='cn')
print(f"  找到 {len(results)} 张卡牌")
if results:
    for card in results[:3]:
        print(f"    - {card.get('card_no')}: {card.get('card_name')}")
