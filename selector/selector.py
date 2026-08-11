#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selector.py — 从融合题库为用户筛选 120 题
用法:
    python selector.py --profile profile.json --bank ../question-bank/items.jsonl --out test120.json
输入:
    profile.json  符合 profile-schema.json 的用户信息
    items.jsonl   融合题库
输出:
    test120.json  {profile, questions[120], coverage_report, selection_reasons}
"""
import json, argparse, hashlib, random, re
from collections import Counter, defaultdict

# purpose/current_state/role → applicable_states 映射
PURPOSE_TO_STATES = {
    'career-planning': ['career-choice','career-transition','mid-career'],
    'study-direction': ['study-direction','graduate-school'],
    'study-abroad-planning': ['study-abroad'],
    'graduate-school-planning': ['graduate-school','academic-stress'],
    'self-exploration': ['self-exploration'],
    'relationship-insight': ['relationship-conflict'],
    'leadership-growth': ['leadership-growth','mid-career'],
    'entrepreneur-fit': ['entrepreneur-stage'],
    'academic-stress-relief': ['academic-stress'],
    'parent-understanding-child': ['parenting-teen'],
}
ROLE_TO_STATES = {
    'student-junior-high': ['academic-stress','study-direction'],
    'student-senior-high': ['academic-stress','study-direction','graduate-school'],
    'student-undergrad': ['fresh-grad','study-direction','graduate-school','study-abroad'],
    'student-grad': ['graduate-school','career-choice','study-abroad'],
    'student-phd': ['academic-stress','career-choice'],
    'employed': ['mid-career','career-transition','leadership-growth'],
    'freelancer': ['entrepreneur-stage','career-transition','life-transition'],
    'entrepreneur': ['entrepreneur-stage','leadership-growth'],
    'parent': ['parenting-teen','life-transition'],
    'job-seeker': ['career-choice','fresh-grad','career-transition'],
}
STATE_TO_STATES = {
    'stable': [],
    'transition': ['career-transition','life-transition'],
    'stress': ['academic-stress','mid-career'],
    'stuck': ['self-exploration','life-transition'],
    'growth-seeking': ['leadership-growth','self-exploration'],
}

CATEGORIES = ['interpersonal-relationship','decision-making','stress-response','motivation-value',
              'learning-cognition','work-career','emotion-self','action-habit',
              'future-vision','conflict-choice']

# 覆盖要求
MIN_ENNEAGRAM_PER_TYPE = 5
MIN_MBTI_PER_POLE = 4
MIN_HOLLAND_PER_TYPE = 2  # R型在题库中仅68题，按比例2/100足够
MIN_HOLLAND_R = 1  # R型题库偏少，单独降门槛
MIN_GALLUP_PER_DOMAIN = 8
MIN_REVERSE = 12
DIFF_TARGET = {2: 36, 3: 54, 4: 24, 5: 6}  # 难度1不进卷，120题按比例


def load_profile(path):
    with open(path, 'r', encoding='utf-8') as f:
        p = json.load(f)
    for req in ('age', 'role', 'purpose'):
        if req not in p or p[req] in (None, ''):
            raise ValueError(f"profile 缺少必填字段: {req}")
    return p


def load_bank(path):
    items = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def target_states(profile):
    ts = set()
    ts |= set(PURPOSE_TO_STATES.get(profile['purpose'], []))
    ts |= set(ROLE_TO_STATES.get(profile['role'], []))
    ts |= set(STATE_TO_STATES.get(profile.get('current_state', 'stable'), []))
    return ts


def state_match_score(item, ts):
    s = 0
    aps = set(item.get('applicable_states', []))
    if profile_purpose_in(aps, ts):
        s += 3
    overlap = aps & ts
    s += 2 * len(overlap)
    return s


def profile_purpose_in(aps, ts):
    return bool(aps & ts)


def item_dims(item):
    """题目贡献的维度集合"""
    dims = set()
    for o in item['options']:
        for k in o['score']:
            dims.add(k)
    return dims


def coverage_of(selected):
    en = defaultdict(int); mb = defaultdict(int); ho = defaultdict(int); ga = defaultdict(int)
    for it in selected:
        dims = item_dims(it)
        for d in dims:
            p, sub = d.split('.')
            if p == 'enneagram': en[sub] += 1
            elif p == 'mbti': mb[sub] += 1
            elif p == 'holland': ho[sub] += 1
            elif p == 'gallup': ga[sub] += 1
    return en, mb, ho, ga


def _normalize_stem(stem):
    """标准化题干用于去重比较：去除标点、空格、尾部人称代词"""
    s = re.sub(r'[，。？！,. ?！]', '', stem)
    s = re.sub(r'[（(][^）)]*[）)]', '', s)
    s = s.replace('②', '').strip()
    # 去除尾部的"你"/"我"/"时"等不影响语义的助词
    s = re.sub(r'[你我]$', '', s)
    s = re.sub(r'时$', '', s)
    return s


def _is_near_duplicate(stem1, stem2):
    """判断两个题干是否近似重复"""
    n1, n2 = _normalize_stem(stem1), _normalize_stem(stem2)
    if n1 == n2:
        return True
    # 包含关系
    if len(n1) > 4 and len(n2) > 4 and (n1 in n2 or n2 in n1):
        return True
    return False


def select(profile, bank, seed=None):
    if seed is None:
        # 不用内置 hash(): 其带进程级哈希盐, 重启后同 profile 出题不同。
        # 用 md5 派生稳定 seed, 保证跨进程确定性。
        digest = hashlib.md5(
            json.dumps(profile, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        seed = int(digest, 16)
    rng = random.Random(seed)
    ts = target_states(profile)

    # Step 1: 打分
    scored = [(state_match_score(it, ts), it) for it in bank]

    # Step 2: 类别配额 —— 每类先取分数最高的前 10 题
    by_cat = defaultdict(list)
    for s, it in scored:
        by_cat[it['category']].append((s, it))
    for c in by_cat:
        by_cat[c].sort(key=lambda x: (-x[0], -x[1]['difficulty']))

    selected = []
    selected_ids = set()
    for c in CATEGORIES:
        pool = by_cat.get(c, [])
        take = pool[:10]
        for s, it in take:
            selected.append(it)
            selected_ids.add(it['id'])

    # 剩余 20 题：全局分数最高且未选，限制每类不超过 14 题
    cat_count = Counter(it['category'] for it in selected)
    remaining = sorted(scored, key=lambda x: -x[0])
    for s, it in remaining:
        if len(selected) >= 120:
            break
        if it['id'] not in selected_ids and cat_count.get(it['category'], 0) < 14:
            # 去重检查
            is_dup = any(_is_near_duplicate(sel['stem'], it['stem']) for sel in selected)
            if is_dup:
                continue
            selected.append(it)
            selected_ids.add(it['id'])
            cat_count[it['category']] += 1

    # Step 2.5: 近似题去重 — 替换近似重复的题干
    dedup_replaced = 0
    i = 0
    while i < len(selected):
        j = i + 1
        while j < len(selected):
            if _is_near_duplicate(selected[i]['stem'], selected[j]['stem']):
                # 保留 state_match_score 更高的，替换另一个
                worse = selected[j] if state_match_score(selected[i], ts) >= state_match_score(selected[j], ts) else selected[i]
                better_idx = j if state_match_score(selected[i], ts) < state_match_score(selected[j], ts) else i
                selected_ids.discard(worse['id'])
                selected.remove(worse)
                # 找替代题
                replacement = None
                for s, it in sorted(scored, key=lambda x: -x[0]):
                    if it['id'] not in selected_ids and it['id'] != worse['id']:
                        # 检查替代题不和已有题重复
                        is_dup = False
                        for sel in selected:
                            if _is_near_duplicate(sel['stem'], it['stem']):
                                is_dup = True
                                break
                        if not is_dup:
                            replacement = it
                            break
                if replacement:
                    selected.append(replacement)
                    selected_ids.add(replacement['id'])
                    dedup_replaced += 1
                # 不递增 j，因为 selected[j] 已被移除
            else:
                j += 1
        i += 1

    # Step 3: 维度覆盖校验与替换
    def try_fix(coverage_ok, dim_pool_pred):
        nonlocal selected, selected_ids
        if coverage_ok():
            return
        cands = [it for it in bank if it['id'] not in selected_ids and dim_pool_pred(it)]
        cands.sort(key=lambda it: -state_match_score(it, ts))
        for c in cands:
            # 检查不引入近似重复
            is_dup = any(_is_near_duplicate(sel['stem'], c['stem']) for sel in selected)
            if is_dup:
                continue
            # 检查不超出类别上限
            cat_count = Counter(it['category'] for it in selected)
            if cat_count.get(c['category'], 0) >= 16:
                continue
            # 只从超额类别(>8题)中淘汰状态分最低的题，保住类别配额底线
            evictable = [it for it in selected if cat_count[it['category']] > 10]
            if not evictable:
                return
            worst = min(evictable, key=lambda it: state_match_score(it, ts))
            selected.remove(worst)
            selected_ids.discard(worst['id'])
            selected.append(c)
            selected_ids.add(c['id'])
            if coverage_ok():
                return

    def en_ok():
        en, *_ = coverage_of(selected)
        return all(en.get(f'type{i}', 0) >= MIN_ENNEAGRAM_PER_TYPE for i in range(1, 10))
    def mb_ok():
        _, mb, *_ = coverage_of(selected)
        return all(mb.get(p, 0) >= MIN_MBTI_PER_POLE for p in 'EISNTFJP')
    def ho_ok():
        *_, ho, _ = coverage_of(selected)
        return all(ho.get(t, 0) >= (MIN_HOLLAND_R if t == 'R' else MIN_HOLLAND_PER_TYPE) for t in 'RIASEC')
    def ga_ok():
        *_, ga = coverage_of(selected)
        return all(ga.get(d, 0) >= MIN_GALLUP_PER_DOMAIN
                   for d in ['executing', 'influencing', 'relationship_building', 'strategic_thinking'])

    try_fix(en_ok, lambda it: any(k.startswith('enneagram.') for o in it['options'] for k in o['score']))
    try_fix(mb_ok, lambda it: any(k.startswith('mbti.') for o in it['options'] for k in o['score']))
    try_fix(ho_ok, lambda it: any(k.startswith('holland.') for o in it['options'] for k in o['score']))
    try_fix(ga_ok, lambda it: any(k.startswith('gallup.') for o in it['options'] for k in o['score']))

    # Step 4: reverse 题补足
    rev_count = sum(1 for it in selected if it.get('reverse'))
    if rev_count < MIN_REVERSE:
        cands = [it for it in bank if it.get('reverse') and it['id'] not in selected_ids]
        cands.sort(key=lambda it: -state_match_score(it, ts))
        for c in cands[:MIN_REVERSE - rev_count]:
            worst = min((it for it in selected if not it.get('reverse')),
                        key=lambda it: state_match_score(it, ts), default=None)
            if worst is None:
                break
            selected.remove(worst)
            selected_ids.discard(worst['id'])
            selected.append(c)
            selected_ids.add(c['id'])

    # Step 5: 排序 —— 类别交错 + 难度递增
    by_cat2 = defaultdict(list)
    for it in selected:
        by_cat2[it['category']].append(it)
    for c in by_cat2:
        by_cat2[c].sort(key=lambda it: it['difficulty'])

    ordered = []
    pools = {c: list(v) for c, v in by_cat2.items()}
    last_cat = None
    while pools:
        cats_avail = [c for c in pools if pools[c] and c != last_cat]
        if not cats_avail:
            cats_avail = [c for c in pools if pools[c]]
        if not cats_avail:
            break
        # 选剩余题难度最低的类，让整体难度递增
        c = min(cats_avail, key=lambda x: pools[x][0]['difficulty'] + rng.random() * 0.5)
        ordered.append(pools[c].pop(0))
        if not pools[c]:
            del pools[c]
        last_cat = c

    return ordered


def build_report(profile, ordered):
    en, mb, ho, ga = coverage_of(ordered)
    themes = Counter()
    for it in ordered:
        for t in it.get('gallup_themes', []):
            themes[t] += 1
    report = {
        'enneagram': {f'type{i}': en.get(f'type{i}', 0) for i in range(1, 10)},
        'mbti': {p: mb.get(p, 0) for p in 'EISNTFJP'},
        'holland': {t: ho.get(t, 0) for t in 'RIASEC'},
        'gallup': {d: ga.get(d, 0) for d in ['executing', 'influencing', 'relationship_building', 'strategic_thinking']},
        'gallup_top_themes': [t for t, _ in themes.most_common(10)],
        'reverse_count': sum(1 for it in ordered if it.get('reverse')),
        'difficulty_dist': dict(sorted(Counter(it['difficulty'] for it in ordered).items())),
        'category_dist': dict(sorted(Counter(it['category'] for it in ordered).items())),
    }
    # 达标检查
    checks = {
        'enneagram_all_types>=5': all(v >= MIN_ENNEAGRAM_PER_TYPE for v in report['enneagram'].values()),
        'mbti_all_poles>=4': all(v >= MIN_MBTI_PER_POLE for v in report['mbti'].values()),
        'holland_all_types>=2(R>=1)': all(ho.get(t, 0) >= (MIN_HOLLAND_R if t == 'R' else MIN_HOLLAND_PER_TYPE) for t in 'RIASEC'),
        'gallup_all_domains>=8': all(v >= MIN_GALLUP_PER_DOMAIN for v in report['gallup'].values()),
        'reverse>=12': report['reverse_count'] >= MIN_REVERSE,
    }
    report['checks'] = checks
    report['all_passed'] = all(checks.values())
    return report


def selection_reason(profile, item):
    ts = target_states(profile)
    hits = set(item.get('applicable_states', [])) & ts
    if hits:
        return f"匹配当前状态：{','.join(sorted(hits))}"
    return f"覆盖{item['category']}维度，保证四体系均衡"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profile', required=True)
    ap.add_argument('--bank', default='../question-bank/items.jsonl')
    ap.add_argument('--out', default='test100.json')
    ap.add_argument('--seed', type=int, default=None)
    args = ap.parse_args()

    profile = load_profile(args.profile)
    bank = load_bank(args.bank)
    ordered = select(profile, bank, seed=args.seed)
    report = build_report(profile, ordered)

    out = {
        'profile': profile,
        'total_questions': len(ordered),
        'questions': ordered,
        'selection_reasons': {it['id']: selection_reason(profile, it) for it in ordered},
        'coverage_report': report,
    }
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"筛选完成: {len(ordered)} 题 -> {args.out}")
    print(f"覆盖达标: {report['all_passed']}")
    for k, v in report['checks'].items():
        print(f"  {'✓' if v else '✗'} {k}")


if __name__ == '__main__':
    main()
