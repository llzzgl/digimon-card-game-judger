#!/usr/bin/env python3
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

data = json.load(open('skill/data/name_aliases.json', 'r', encoding='utf-8'))
print(f'Variants: {len(data["variants"])}')
print(f'JP to CN: {len(data["jp_to_cn"])}')
print('\nSample JP→CN:')
for k, v in list(data['jp_to_cn'].items())[:30]:
    print(f'  {k} → {v}')
