"""检查卡牌是否在数据库中"""
import json
from pathlib import Path

# 直接在 JSON 文件中搜索
data_dir = Path('../digimon_card_data')
target_cards = ['BT20-079', 'BT23-058']

print("=== 在原始 JSON 文件中搜索 ===")
for f in data_dir.glob('*cards.json'):
    content = f.read_text(encoding='utf-8')
    for target in target_cards:
        if target in content:
            data = json.loads(content)
            for card in data:
                if card.get('card_no') == target:
                    print(f"文件: {f.name}")
                    print(f"卡号: {card.get('card_no')}")
                    print(f"名称: {card.get('card_name')}")
                    effect = card.get('effect', '无')
                    print(f"效果: {effect}")
                    print("---")
