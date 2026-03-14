#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix V 仔 alias mapping - EXPLICIT no space"""

import json

with open('skill/data/name_aliases.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Explicitly construct the value WITHOUT space
# V + 仔 + 兽 (no spaces)
correct_value = 'V' + '仔' + '兽'
print(f"Correct value: {repr(correct_value)}")
print(f"Correct value bytes: {correct_value.encode('utf-8')}")

# Remove any existing V 仔 entries
for key in list(data['variants'].keys()):
    if 'V' in key and '仔' in key:
        print(f"Removing old key: {repr(key)} -> {repr(data['variants'][key])}")
        del data['variants'][key]

# Add correct mapping
data['variants']['V 仔'] = correct_value
print(f"\nAdded: 'V 仔' -> {repr(correct_value)}")

with open('skill/data/name_aliases.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\nFile updated successfully")
