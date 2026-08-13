#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_age_multidim.py — 补充年龄段覆盖 + 多维度测量 + 新量表类型
生成 120 道新题，解决三大缺口：
  A. 家长视角题目（30题）
  B. 青少年专属题目（25题）
  C. 新量表类型（25题）— likert-5/likert-7/ranking
  D. 四体系多维度题目（40题）— 提升holland覆盖和跨体系测量
"""
import json, re, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ITEMS_PATH = os.path.join(SCRIPT_DIR, 'items.jsonl')

# 加载现有题干用于查重
existing_normalized = set()
max_id = 0
with open(ITEMS_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        q = json.loads(line)
        ns = re.sub(r'[，。？！,. ?！]', '', q['stem'])
        ns = re.sub(r'[（(][^）)]*[）)]', '', ns)
        existing_normalized.add(ns)
        qid = int(q['id'][1:])
        if qid > max_id:
            max_id = qid

next_id = max_id + 1
print(f"现有题库: {len(existing_normalized)} 题, max_id=Q{max_id:04d}, 起始ID=Q{next_id:04d}")

# 导入题目定义
from questions_age_multidim import NEW_QUESTIONS

# 去重检查
dup_count = 0
valid_questions = []
for q in NEW_QUESTIONS:
    ns = re.sub(r'[，。？！,. ?！]', '', q['stem'])
    ns = re.sub(r'[（(][^）)]*[）)]', '', ns)
    if ns in existing_normalized:
        dup_count += 1
        print(f"  [重复] 跳过: {q['stem']}")
        continue
    existing_normalized.add(ns)
    valid_questions.append(q)

print(f"新题定义: {len(NEW_QUESTIONS)} 题, 去重后: {len(valid_questions)} 题, 重复: {dup_count} 题")

# 分配ID并补充默认字段
for i, q in enumerate(valid_questions):
    q['id'] = f"Q{next_id + i:04d}"
    q['systems'] = ["enneagram", "mbti", "holland", "gallup"]
    q.setdefault('reverse', False)
    q.setdefault('source', 'ai-generated')

# 验证
errors = []
valid_enneagram = {f"enneagram.type{n}" for n in range(1,10)}
valid_mbti = {"mbti.E","mbti.I","mbti.S","mbti.N","mbti.T","mbti.F","mbti.J","mbti.P"}
valid_holland = {"holland.R","holland.I","holland.A","holland.S","holland.E","holland.C"}
valid_gallup = {"gallup.executing","gallup.influencing","gallup.relationship_building","gallup.strategic_thinking"}
valid_themes = {"achiever","activator","adaptability","analytical","arranger","belief","command","communication",
    "competition","connectedness","context","consistency","deliberative","developer","discipline","empathy",
    "focus","futuristic","harmony","ideation","includer","individualization","input","intellection",
    "learner","maximizer","positivity","relator","responsibility","restorative","self-assurance",
    "significance","strategic","woo"}
valid_categories = {"interpersonal-relationship","decision-making","stress-response","motivation-value",
    "learning-cognition","work-career","emotion-self","action-habit","future-vision","conflict-choice"}
valid_states = {"career-choice","career-transition","study-direction","study-abroad","graduate-school",
    "academic-stress","self-exploration","relationship-conflict","leadership-growth","entrepreneur-stage",
    "fresh-grad","mid-career","parenting-teen","life-transition"}
valid_scales = {"likert-4","likert-5","likert-7","forced-choice","ranking"}

for q in valid_questions:
    qid = q['id']
    if q['category'] not in valid_categories:
        errors.append(f"{qid}: 无效category '{q['category']}'")
    if q['scale'] not in valid_scales:
        errors.append(f"{qid}: 无效scale '{q['scale']}'")
    if len(q['systems']) < 2:
        errors.append(f"{qid}: systems不足2个")
    for opt in q['options']:
        for key in opt.get('score', {}):
            if key not in valid_enneagram | valid_mbti | valid_holland | valid_gallup:
                errors.append(f"{qid}: 无效score key '{key}'")
    for theme in q.get('gallup_themes', []):
        if theme not in valid_themes:
            errors.append(f"{qid}: 无效gallup_theme '{theme}'")
    for state in q.get('applicable_states', []):
        if state not in valid_states:
            errors.append(f"{qid}: 无效applicable_state '{state}'")
    if not (1 <= q['difficulty'] <= 5):
        errors.append(f"{qid}: difficulty超出范围 {q['difficulty']}")
    if len(q['stem']) > 30:
        errors.append(f"{qid}: 题干超长({len(q['stem'])}字): {q['stem']}")

if errors:
    print(f"\n验证发现 {len(errors)} 个错误:")
    for e in errors[:20]:
        print(f"  {e}")
    if len(errors) > 20:
        print(f"  ... 还有 {len(errors)-20} 个")
    print("\n请修复后再运行。")
    sys.exit(1)
else:
    print(f"\n验证通过: {len(valid_questions)} 题全部合法")

# 写入
with open(ITEMS_PATH, 'a', encoding='utf-8') as f:
    for q in valid_questions:
        f.write(json.dumps(q, ensure_ascii=False) + '\n')

print(f"\n已追加 {len(valid_questions)} 题到 items.jsonl")
print(f"新ID范围: Q{next_id:04d} ~ Q{next_id + len(valid_questions) - 1:04d}")

# 统计
from collections import Counter
scale_dist = Counter(q['scale'] for q in valid_questions)
cat_dist = Counter(q['category'] for q in valid_questions)
state_dist = Counter()
for q in valid_questions:
    for s in q['applicable_states']:
        state_dist[s] += 1

print(f"\n=== 新题量表分布 ===")
for s, c in scale_dist.most_common():
    print(f"  {s}: {c}")
print(f"\n=== 新题类别分布 ===")
for c, n in cat_dist.most_common():
    print(f"  {c}: {n}")
print(f"\n=== 新题状态分布 ===")
for s, n in state_dist.most_common():
    print(f"  {s}: {n}")

# 验证4体系覆盖
four_sys = sum(1 for q in valid_questions if len(q['systems']) >= 4)
has_holland = sum(1 for q in valid_questions if any(k.startswith('holland') for opt in q['options'] for k in opt.get('score',{})))
has_r = sum(1 for q in valid_questions if any(k=='holland.R' for opt in q['options'] for k in opt.get('score',{})))
print(f"\n=== 多维度统计 ===")
print(f"  4体系覆盖: {four_sys}/{len(valid_questions)}")
print(f"  含holland分数: {has_holland}/{len(valid_questions)}")
print(f"  含holland.R: {has_r}/{len(valid_questions)}")
