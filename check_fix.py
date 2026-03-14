#!/usr/bin/env python3
import json

with open('skill/data/name_aliases.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

v = data['variants'].get('V 仔', 'NOT FOUND')
print(f"Value: {repr(v)}")
if v != 'NOT FOUND':
    print(f"Bytes: {v.encode('utf-8')}")
    print(f"Has space: {' ' in v}")
    
# Also check what the card names look like
with open('skill/data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

vmon_cards = [c for c in cards if 'V 仔' in c.get('card_name', '')][:3]
print(f"\nActual card names:")
for c in vmon_cards:
    name = c['card_name']
    print(f"  {repr(name)}: {name.encode('utf-8')}")
