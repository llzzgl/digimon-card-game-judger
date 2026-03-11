"""检查QA数据结构"""
import json
import re

# 加载QA数据
with open('../official_qa_jp.json', 'r', encoding='utf-8') as f:
    qa_data = json.load(f)

print(f"总QA数量: {len(qa_data)}")

# 检查包含card_name的QA
qa_with_card_name = [q for q in qa_data if 'card_name' in q and q['card_name']]
print(f"\n包含card_name的QA: {len(qa_with_card_name)}")

# 显示示例
print("\n示例QA:")
for i, q in enumerate(qa_with_card_name[:5], 1):
    print(f"\n{i}. card_name: {q.get('card_name')}")
    print(f"   question: {q['question'][:80]}...")
    
    # 尝试从card_name中提取编号（修复正则表达式）
    card_name = q.get('card_name', '')
    # 匹配格式：EX11-011, BT1-001, ST1-01等
    pattern = re.compile(r'\b((?:BT|ST|EX|P|RB|LM)\d{1,2}-\d{2,3})\b', re.IGNORECASE)
    matches = pattern.findall(card_name)
    if matches:
        print(f"   提取的编号: {matches}")

# 检查其他可能包含卡牌编号的字段
print("\n\n检查QA数据的所有字段:")
if qa_data:
    print(f"字段: {list(qa_data[0].keys())}")
    
# 统计有多少QA包含可提取的卡牌编号
pattern = re.compile(r'\b((?:BT|ST|EX|P|RB|LM)\d{1,2}-\d{2,3})\b', re.IGNORECASE)
qa_with_extractable_cards = [q for q in qa_data if 'card_name' in q and pattern.search(q.get('card_name', ''))]
print(f"\n可提取卡牌编号的QA: {len(qa_with_extractable_cards)}")

# 测试从问题和答案中提取
qa_with_cards_in_content = []
for q in qa_data:
    content = q.get('question', '') + ' ' + q.get('answer', '')
    if pattern.search(content):
        qa_with_cards_in_content.append(q)

print(f"问题/答案中包含卡牌编号的QA: {len(qa_with_cards_in_content)}")
