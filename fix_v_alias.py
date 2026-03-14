#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix V 仔 alias mapping - remove space from value"""

import json

with open('skill/data/name_aliases.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# The issue: 'V 仔' (with space) maps to 'V 仔兽' (with space)
# But card names are 'V 仔兽' (no space)
# Fix: map to 'V 仔兽' (no space)

# Remove the old entry with space in value
if 'V 仔' in data['variants']:
    del data['variants']['V 仔']

# Add correct mapping (no space in value)
data['variants']['V 仔'] = 'V 仔兽'

with open('skill/data/name_aliases.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed: 'V 仔' -> 'V 仔兽' (no space in value)")
print(f"Value bytes: {'V 仔兽'.encode('utf-8')}")
