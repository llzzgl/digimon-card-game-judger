"""测试卡牌搜索功能"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("测试卡牌搜索功能")
print("=" * 80)

from main_new import NewCardGameJudge

print("\n初始化系统...")
judge = NewCardGameJudge()

print("\n" + "=" * 80)
print("测试卡牌搜索")
print("=" * 80)

test_cards = [
    'EX08-074',  # 标准化格式
    'EX8-074',   # 原始格式
    'EX11-024',  # 另一张卡
    'P-165',     # P系列
    'P-001',     # P系列补零
]

for card_no in test_cards:
    card = judge.search_card(card_no)
    if card:
        print(f"✅ {card_no}: 找到 - {card.get('name_cn', card.get('name_jp', 'N/A'))}")
    else:
        print(f"❌ {card_no}: 未找到")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
