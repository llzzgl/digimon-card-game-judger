# -*- coding: utf-8 -*-
"""Check V-mon aliases and fix if needed"""

import json

# Load aliases
aliases = json.load(open('skill/data/name_aliases.json', 'r', encoding='utf-8'))
variants = aliases.get('variants', {})

# Find all V-related aliases
print("=== V-related Aliases ===")
v_keys = [k for k in variants.keys() if 'V' in k]
for k in sorted(v_keys):
    v = variants[k]
    print(f"  '{k}' -> '{v}'")
    print(f"    bytes: {k.encode('utf-8')} -> {v.encode('utf-8')}")

# Check specific aliases we need
print("\n=== Required Aliases ===")
required = {
    'V 仔': 'V 仔兽',
    'V': 'V 仔兽',
}

for alias, target in required.items():
    if alias in variants:
        actual = variants[alias]
        status = "OK" if actual == target else f"WRONG (got '{actual}')"
        print(f"  '{alias}' -> '{target}': {status}")
    else:
        print(f"  '{alias}' -> '{target}': MISSING")

# Check card names
print("\n=== V-mon Cards ===")
cards = json.load(open('skill/data/cards.json', 'r', encoding='utf-8'))
vmon_cards = [c for c in cards if 'ブイモン' in c.get('card_name_jp', '')]
print(f"Found {len(vmon_cards)} V-mon cards")
for c in vmon_cards[:5]:
    print(f"  {c['card_no']}: {c['card_name']}")

# Check if we need to add aliases
print("\n=== Fix Needed? ===")
if 'V 仔' not in variants:
    print("YES - Need to add 'V 仔' -> 'V 仔兽' alias")
else:
    print("NO - Alias already exists")
