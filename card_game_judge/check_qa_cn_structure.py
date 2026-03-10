"""检查中文QA数据结构"""
import json
import re

# 加载QA数据
with open('card_game_QA_manger/official_qa_cn_qwen.json', 'r', encoding='utf-8') as f:
    qa_data = json.load(f)

print(f"总QA数量: {len(qa_data)}")

# 检查字段
if qa_data:
    print(f"\n字段: {list(qa_data[0].keys())}")

# 检查是否有card_name字段
qa_with_card_name = [q for q in qa_data if 'card_name' in q and q['card_name']]
print(f"\n包含card_name字段的QA: {len(qa_with_card_name)}")

# 从问题和答案中提取卡牌编号
pattern = re.compile(r'\b((?:BT|ST|EX|P|RB|LM)\d{1,2}-\d{2,3})\b', re.IGNORECASE)
qa_with_cards_in_content = []
for q in qa_data:
    content = q.get('question', '') + ' ' + q.get('answer', '')
    if pattern.search(content):
        qa_with_cards_in_content.append(q)

print(f"\n问题/答案中包含卡牌编号的QA: {len(qa_with_cards_in_content)}")

# 显示示例
print("\n示例QA（包含卡牌编号）:")
for i, q in enumerate(qa_with_cards_in_content[:5], 1):
    content = q.get('question', '') + ' ' + q.get('answer', '')
    matches = pattern.findall(content)
    print(f"\n{i}. 提取的编号: {matches}")
    print(f"   问题: {q['question'][:80]}...")
    print(f"   答案: {q['answer'][:80]}...")

# 检查原始日文QA是否有card_name
print("\n\n检查原始日文QA文件...")
try:
    with open('../official_qa_jp.json', 'r', encoding='utf-8') as f:
        qa_jp = json.load(f)
    
    qa_jp_with_card_name = [q for q in qa_jp if 'card_name' in q and q['card_name']]
    print(f"日文QA总数: {len(qa_jp)}")
    print(f"包含card_name的日文QA: {len(qa_jp_with_card_name)}")
    
    if qa_jp_with_card_name:
        print("\n日文QA示例:")
        for i, q in enumerate(qa_jp_with_card_name[:3], 1):
            print(f"\n{i}. card_name: {q.get('card_name')}")
            print(f"   qa_number: {q.get('qa_number')}")
            
            # 尝试从card_name中提取编号
            card_name = q.get('card_name', '')
            matches = pattern.findall(card_name)
            if matches:
                print(f"   提取的编号: {matches}")
except Exception as e:
    print(f"无法读取日文QA: {e}")

# 检查是否可以通过qa_number关联
print("\n\n检查qa_number关联:")
if qa_data and qa_jp:
    # 找一个中文QA
    cn_qa = qa_data[0]
    cn_qa_number = cn_qa.get('qa_number')
    
    # 在日文QA中查找相同的qa_number
    jp_qa = next((q for q in qa_jp if q.get('qa_number') == cn_qa_number), None)
    
    if jp_qa:
        print(f"✅ 可以通过qa_number关联")
        print(f"   中文QA qa_number: {cn_qa_number}")
        print(f"   日文QA qa_number: {jp_qa.get('qa_number')}")
        print(f"   日文QA card_name: {jp_qa.get('card_name', 'N/A')}")
    else:
        print(f"❌ 无法通过qa_number关联")
