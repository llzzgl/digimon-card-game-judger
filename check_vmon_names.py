#!/usr/bin/env python3
import json

with open('skill/data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Find cards with V in the name
v_cards = [c for c in cards if 'V' in c.get('card_name', '') or 'v' in c.get('card_name', '')]
print(f"Cards with V/v in name: {len(v_cards)}")

# Show first 10
for c in v_cards[:10]:
    name = c['card_name']
    print(f"  {repr(name)}: {name.encode('utf-8')}")

# Find cards with ブイモン in Japanese name
jp_vmon = [c for c in cards if 'ブイモン' in c.get('card_name_jp', '')]
print(f"\nCards with ブイモン in JP name: {len(jp_vmon)}")
for c in jp_vmon[:5]:
    print(f"  {c['card_no']}: {repr(c['card_name'])} = {c['card_name'].encode('utf-8')}")
