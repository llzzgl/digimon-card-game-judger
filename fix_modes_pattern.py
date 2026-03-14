#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix modes.py patterns - remove spaces"""

with open('src/judger/api/modes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the patterns - remove spaces after Chinese characters
old_patterns = """    answer_patterns = [
        r'原答案说 (.*?)(?:，|但|$)',  # 原答案说...（，|但 | 结束）
        r'原答案 [说称是](.*?)(?:，|。|但|$)',  # 原答案说/称/是...
        r'之前的回答 [说称是](.*?)(?:，|。|$)',  # 之前的回答...
        r'错误 [:：](.*?)(?:，|。|$)',  # 错误：...
        r'说 (.*?)(?:，|。|但|$)',  # 说...（通用匹配）
    ]"""

new_patterns = """    answer_patterns = [
        r'原答案说 (.*?)(?:，|但|$)',  # 原答案说...（，|但 | 结束）
        r'原答案 [说称是](.*?)(?:，|。|但|$)',  # 原答案说/称/是...
        r'之前的回答 [说称是](.*?)(?:，|。|$)',  # 之前的回答...
        r'错误 [:：](.*?)(?:，|。|$)',  # 错误：...
        r'说 (.*?)(?:，|。|但|$)',  # 说...（通用匹配）
    ]"""

if old_patterns in content:
    content = content.replace(old_patterns, new_patterns)
    with open('src/judger/api/modes.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed patterns in modes.py")
else:
    print("Pattern not found - checking current content...")
    # Find and show the answer_patterns section
    idx = content.find('answer_patterns')
    if idx >= 0:
        print(content[idx:idx+400])
