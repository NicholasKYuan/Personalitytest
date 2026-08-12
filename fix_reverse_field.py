#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复题库中 reverse=None 的题目，将其设为 False。
- reverse 字段纯为元数据（分数已在选项中预映射）
- 已有 373 道 reverse=True，远超 selector 的 MIN_REVERSE=12 需求
- None→False 是最安全的默认值
"""
import json

INPUT = 'question-bank/items.jsonl'
fixed = 0
total = 0

with open(INPUT, 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open(INPUT, 'w', encoding='utf-8') as f:
    for line in lines:
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        total += 1
        if item.get('reverse') is None:
            item['reverse'] = False
            fixed += 1
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f'总题数: {total}')
print(f'修复 None→False: {fixed}')
print(f'reverse=True: {sum(1 for l in lines if l.strip() and json.loads(l.strip()).get("reverse") is True)}')
print(f'reverse=False: {sum(1 for l in lines if l.strip() and json.loads(l.strip()).get("reverse") is False)}')
print(f'reverse=None: 0 (已全部修复)')
