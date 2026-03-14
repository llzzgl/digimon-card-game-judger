#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix modes.py patterns - use Unicode escapes that work"""

with open('src/judger/api/modes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the answer_patterns section
# Using Unicode escapes which we know work in regex
old_start = "    # 尝试提取答案引用"
old_end = "    ]"

start_idx = content.find(old_start)
if start_idx >= 0:
    # Find the end of the answer_patterns list
    end_idx = content.find(old_end, start_idx)
    if end_idx >= 0:
        end_idx = content.find("]", end_idx) + 1  # Include the closing bracket
        
        new_patterns = '''    # 尝试提取答案引用（如 "原答案说..."）
    # 使用 Unicode 转义序列（在 regex 中会被正确解释）
    answer_patterns = [
        r'\\u539f\\u7b54\\u6848\\u8bf4(.*?)(?:\\uff0c|\\u4f46|$)',  # 原答案说...（，|但 | 结束）
        r'\\u539f\\u7b54\\u6848[\\u8bf4\\u79f0\\u662f](.*?)(?:\\uff0c|\\u3002|\\u4f46|$)',  # 原答案说/称/是...
        r'\\u4e4b\\u524d\\u7684\\u56de\\u7b54[\\u8bf4\\u79f0\\u662f](.*?)(?:\\uff0c|\\u3002|$)',  # 之前的回答...
        r'\\u9519\\u8bef[\\uff1a:](.*?)(?:\\uff0c|\\u3002|$)',  # 错误：...
        r'\\u8bf4(.*?)(?:\\uff0c|\\u3002|\\u4f46|$)',  # 说...（通用匹配）
    ]'''
        
        content = content[:start_idx] + new_patterns + content[end_idx:]
        
        with open('src/judger/api/modes.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed modes.py with Unicode escape patterns")
    else:
        print("Could not find end of patterns")
else:
    print("Could not find start of patterns")
