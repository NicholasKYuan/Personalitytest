#!/usr/bin/env python3
"""
题库质量验证脚本
用法: python question-bank/validate_questions.py
"""
import json
import collections
import sys
import os

def load_items(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), 'items.jsonl')
    items = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items

def get_opt_dims(opt):
    dims = set()
    for key in opt.get('score', {}):
        dim = key.split('.')[0]
        dims.add(dim)
    return dims

def validate(items):
    errors = []
    warnings = []
    
    # 1. ID 唯一性
    id_counts = collections.Counter(it['id'] for it in items)
    for id_, cnt in id_counts.items():
        if cnt > 1:
            errors.append(f'ID重复: {id_} 出现 {cnt} 次')
    
    # 2. forced-choice 选项重复检测
    fc_items = [it for it in items if it.get('scale') == 'forced-choice']
    opt_groups = collections.defaultdict(list)
    for it in fc_items:
        opts = tuple(opt['text'] for opt in it.get('options', []))
        opt_groups[opts].append(it)
    
    for opts, group in opt_groups.items():
        if len(group) >= 2:
            ids = [it['id'] for it in group]
            errors.append(f'选项重复组 ({len(group)}题): {ids}')
            print(f'  选项: {list(opts)[:2]}...')
    
    # 3. 维度覆盖检测
    for it in items:
        all_dims = set()
        for opt in it.get('options', []):
            all_dims |= get_opt_dims(opt)
        
        if len(all_dims) < 3:
            warnings.append(f'{it["id"]}: 只覆盖 {all_dims} ({len(all_dims)}个维度) - {it["stem"][:30]}')
        
        if 'holland' not in all_dims:
            warnings.append(f'{it["id"]}: 缺少 holland 维度 - {it["stem"][:30]}')
    
    # 4. Score key 格式检测
    valid_dims = {'enneagram', 'mbti', 'gallup', 'holland'}
    valid_enneagram = {f'type{i}' for i in range(1, 10)}
    valid_mbti = {'E', 'I', 'S', 'N', 'T', 'F', 'J', 'P'}
    valid_gallup = {'executing', 'influencing', 'relationship_building', 'strategic_thinking'}
    valid_holland = {'R', 'I', 'A', 'S', 'E', 'C'}
    
    # gallup 主题名黑名单（不应出现在 score key 中）
    gallup_themes = {
        'command', 'harmony', 'adaptability', 'woo', 'empathy', 'developer',
        'includer', 'significance', 'focus', 'analytical', 'deliberative',
        'learner', 'input', 'ideation', 'strategic', 'futuristic', 'self-awareness',
        'responsibility', 'discipline', 'arranger', 'arranger', 'competition',
        'connectedness', 'altruism', 'open-mindedness', 'perseverance',
        'intuition', 'self-reliance', 'fairness', 'trust'
    }
    
    for it in items:
        for opt in it.get('options', []):
            for key in opt.get('score', {}):
                parts = key.split('.')
                if len(parts) < 2:
                    errors.append(f'{it["id"]}: 错误key格式 "{key}"')
                    continue
                
                dim = parts[0]
                sub = parts[1] if len(parts) > 1 else ''
                
                if dim not in valid_dims:
                    errors.append(f'{it["id"]}: 未知维度 "{dim}" in key "{key}"')
                
                if dim == 'gallup' and sub in gallup_themes:
                    errors.append(f'{it["id"]}: gallup主题名误用为score key "{key}" (应为 gallup.executing/influencing/relationship_building/strategic_thinking)')
                
                if dim == 'enneagram' and sub not in valid_enneagram:
                    errors.append(f'{it["id"]}: 错误enneagram类型 "{sub}" in key "{key}"')
                
                if dim == 'mbti' and sub not in valid_mbti:
                    errors.append(f'{it["id"]}: 错误MBTI极 "{sub}" in key "{key}"')
                
                if dim == 'gallup' and sub not in valid_gallup:
                    errors.append(f'{it["id"]}: 错误gallup领域 "{sub}" in key "{key}"')
                
                if dim == 'holland' and sub not in valid_holland:
                    errors.append(f'{it["id"]}: 错误holland类型 "{sub}" in key "{key}"')
    
    # 5. 必填字段检测
    for it in items:
        for field in ['id', 'category', 'systems', 'stem', 'scale', 'options']:
            if field not in it:
                errors.append(f'{it.get("id","?")}: 缺少必填字段 "{field}"')
        
        if 'options' in it and len(it.get('options', [])) < 2:
            warnings.append(f'{it["id"]}: 选项少于2个')
    
    return errors, warnings

def main():
    items = load_items()
    print(f'题库总数: {len(items)}')
    
    errors, warnings = validate(items)
    
    print(f'\n=== 错误 ({len(errors)}) ===')
    for e in errors[:50]:
        print(f'  ❌ {e}')
    if len(errors) > 50:
        print(f'  ... 还有 {len(errors)-50} 条')
    
    print(f'\n=== 警告 ({len(warnings)}) ===')
    for w in warnings[:30]:
        print(f'  ⚠️  {w}')
    if len(warnings) > 30:
        print(f'  ... 还有 {len(warnings)-30} 条')
    
    # 统计
    print(f'\n=== 统计 ===')
    scales = collections.Counter(it.get('scale') for it in items)
    for k, v in scales.most_common():
        print(f'  {k}: {v}')
    
    cats = collections.Counter(it.get('category') for it in items)
    for k, v in cats.most_common():
        print(f'  {k}: {v}')
    
    # 维度覆盖
    dim_coverage = collections.Counter()
    for it in items:
        all_dims = set()
        for opt in it.get('options', []):
            all_dims |= get_opt_dims(opt)
        dim_coverage[len(all_dims)] += 1
    print(f'\n  维度覆盖分布:')
    for k in sorted(dim_coverage.keys()):
        print(f'    {k}个维度: {dim_coverage[k]}题 ({dim_coverage[k]/len(items)*100:.1f}%)')
    
    if errors:
        print(f'\n❌ 有 {len(errors)} 个错误，请修复后再使用')
        sys.exit(1)
    else:
        print(f'\n✅ 无错误，有 {len(warnings)} 个警告')

if __name__ == '__main__':
    main()
