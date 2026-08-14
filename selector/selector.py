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
import json, argparse, random, re
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

# decision_horizon → 偏好的难度范围（用于匹配题目的远见性）
DECISION_HORIZON_DIFFS = {
    'immediate': [1, 2],        # 短期决策 → 偏好低难度、现状类题
    'within-1-year': [2, 3],    # 近期决策 → 中等难度
    '1-3-years': [3, 4],        # 中期决策 → 中高难度、前瞻类
    '3-plus-years': [4, 5],     # 长期决策 → 高难度、远见类
}

CATEGORIES = ['interpersonal-relationship','decision-making','stress-response','motivation-value',
              'learning-cognition','work-career','emotion-self','action-habit',
              'future-vision','conflict-choice']

# 覆盖要求
MIN_ENNEAGRAM_PER_TYPE = 5
MIN_MBTI_PER_POLE = 4
MIN_HOLLAND_PER_TYPE = 2  # RIASEC各型题库均≥268题，2/100足够
MIN_HOLLAND_R = 2  # R型题库现有268题，与其他型持平
MIN_GALLUP_PER_DOMAIN = 15  # 下限提高：原8→15，确保4领域都有足够样本量
MAX_GALLUP_PER_DOMAIN = 65  # 新增上限：120题里单个领域不超过65题，避免strategic_thinking等过载
MIN_GALLUP_INFLUENCING = 20  # influencing题库较少(839题)，单独设更高下限确保不被边缘化
MIN_REVERSE = 10
DIFF_TARGET = {2: 36, 3: 54, 4: 24, 5: 6}  # 难度1不进卷，120题按比例

# 量表多样性要求（5种量表在120题中的最低配额）
MIN_SCALE_DIVERSITY = {
    'forced-choice': 50,   # 主力题型，至少50题
    'likert-4': 10,        # 至少10题（部分profile状态匹配的likert-4题较少）
    'likert-5': 2,         # 新增量表，至少2题（题库仅18题）
    'likert-7': 1,         # 新增量表，至少1题（题库仅11题）
    'ranking': 1,          # 新增量表，至少1题（题库仅12题）
}
# 含holland分数的题目最低数量（holland覆盖已提升至34%+）
MIN_HOLLAND_QUESTIONS = 30


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


def state_match_score(item, ts, decision_horizon=None):
    s = 0
    aps = set(item.get('applicable_states', []))
    if profile_purpose_in(aps, ts):
        s += 3
    overlap = aps & ts
    s += 2 * len(overlap)
    # decision_horizon 匹配：用户决策时间窗口与题目难度/远见性匹配 → +1
    if decision_horizon:
        preferred_diffs = DECISION_HORIZON_DIFFS.get(decision_horizon, [])
        if item.get('difficulty', 0) in preferred_diffs:
            s += 1
    # 多维度奖励：4体系融合题信息量更大，优先选入 → +1
    n_systems = len(set(k.split('.')[0] for o in item['options'] for k in o.get('score', {})))
    if n_systems >= 4:
        s += 1
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
    # 包含关系（长度门槛 >=2，避免"独处"被"独处时你更倾向"漏检）
    if len(n1) >= 2 and len(n2) >= 2 and (n1 in n2 or n2 in n1):
        return True
    return False


def select(profile, bank, seed=None):
    rng = random.Random(seed if seed is not None else hash(json.dumps(profile, sort_keys=True)))
    ts = target_states(profile)
    dh = profile.get('decision_horizon')

    # Step 1: 打分（传入 decision_horizon 以匹配题目难度/远见性）
    scored = [(state_match_score(it, ts, dh), it) for it in bank]

    # Step 2: 类别配额 —— 每类先取分数最高的前 12 题（10类×12=120）
    by_cat = defaultdict(list)
    for s, it in scored:
        by_cat[it['category']].append((s, it))
    for c in by_cat:
        by_cat[c].sort(key=lambda x: (-x[0], -x[1]['difficulty']))

    selected = []
    selected_ids = set()
    for c in CATEGORIES:
        pool = by_cat.get(c, [])
        taken = 0
        for s, it in pool:
            if taken >= 12:
                break
            # 去重检查：不和已选题重复
            is_dup = any(_is_near_duplicate(sel['stem'], it['stem']) for sel in selected)
            if is_dup:
                continue
            selected.append(it)
            selected_ids.add(it['id'])
            taken += 1

    # 剩余题：全局分数最高且未选，限制每类不超过 14 题
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
                # 找替代题（检查类别不超限）
                replacement = None
                cat_count_now = Counter(sel['category'] for sel in selected)
                for s, it in sorted(scored, key=lambda x: -x[0]):
                    if it['id'] not in selected_ids and it['id'] != worse['id']:
                        if cat_count_now.get(it['category'], 0) >= 15:
                            continue
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

    # Step 3.5: 霍兰德覆盖专项补足 —— 确保至少 30 题含 Holland 分数
    def holland_question_count(sel):
        return sum(1 for it in sel if any(k.startswith('holland.') for o in it['options'] for k in o['score']))
    
    while holland_question_count(selected) < MIN_HOLLAND_QUESTIONS:
        # 找含 Holland 分数且未选入的题
        holland_cands = [
            it for it in bank
            if it['id'] not in selected_ids
            and any(k.startswith('holland.') for o in it['options'] for k in o['score'])
        ]
        holland_cands.sort(key=lambda it: -state_match_score(it, ts))
        if not holland_cands:
            break
        # 找不含 Holland 分数且可替换的题（从类别最多的中选）
        cat_count_now = Counter(it['category'] for it in selected)
        replaceable = [
            it for it in selected
            if not any(k.startswith('holland.') for o in it['options'] for k in o['score'])
            and cat_count_now[it['category']] > 8
        ]
        if not replaceable:
            break
        worst = min(replaceable, key=lambda it: state_match_score(it, ts))
        best_holland = holland_cands[0]
        # 去重检查
        is_dup = any(_is_near_duplicate(sel['stem'], best_holland['stem']) for sel in selected)
        if is_dup:
            holland_cands.pop(0)
            continue
        selected.remove(worst)
        selected_ids.discard(worst['id'])
        selected.append(best_holland)
        selected_ids.add(best_holland['id'])

    # Step 3.6: 盖洛普4领域平衡 —— 防止 strategic_thinking 过载、influencing 不足
    # 用户反馈"战略思维容易测出来"，实测120题里 strategic_thinking 高达74题、influencing 仅46题
    # 该步骤会：1. 把超过MAX的领域题换成不足MIN的领域题；2. 单独补足influencing
    def gallup_domain_count_in_item(it):
        """题目含哪些gallup领域"""
        return set(k.split('.')[1] for o in it['options'] for k in o.get('score', {}) if k.startswith('gallup.'))

    def _gallup_protected(it):
        """盖洛普平衡步骤中判断题是否受保护（不应被移除）"""
        # reverse题不移除（reverse题少）
        if it.get('reverse'):
            return True
        # 新量表题不移除（题库少，已被Step 4强制选入）
        if it.get('scale', '') in ('likert-5', 'likert-7', 'ranking'):
            return True
        return False

    GALLUP_DOMAINS = ['executing', 'influencing', 'relationship_building', 'strategic_thinking']

    # 3.6a: 上限约束 - 超过MAX的领域题换成"不超MAX且不过载"的领域题
    # 关键修正：只要某领域超MAX就替换，不再要求其他领域必须低于MIN
    for over_domain in GALLUP_DOMAINS:
        *_, ga_now = coverage_of(selected)
        safety = 0
        while ga_now.get(over_domain, 0) > MAX_GALLUP_PER_DOMAIN and safety < 60:
            safety += 1
            # 找含over_domain的、可替换的题
            replaceable = [
                it for it in selected
                if over_domain in gallup_domain_count_in_item(it)
                and not _gallup_protected(it)
            ]
            if not replaceable:
                break
            # 优先替换只含over_domain不含其他过载领域的题
            replaceable.sort(key=lambda it: (
                state_match_score(it, ts, dh),
                -len(gallup_domain_count_in_item(it) - {over_domain})  # 含其他领域越多越优先保留
            ))
            worst = replaceable[0]
            # 找一个含"非over_domain且非过载"领域、不含over_domain的候选题
            other_domains = [d for d in GALLUP_DOMAINS if d != over_domain and ga_now.get(d, 0) < MAX_GALLUP_PER_DOMAIN]
            if not other_domains:
                other_domains = [d for d in GALLUP_DOMAINS if d != over_domain]
            cands = [
                it for it in bank
                if it['id'] not in selected_ids
                and any(d in gallup_domain_count_in_item(it) for d in other_domains)
                and over_domain not in gallup_domain_count_in_item(it)
                and not any(_is_near_duplicate(sel['stem'], it['stem']) for sel in selected)
            ]
            cands.sort(key=lambda it: -state_match_score(it, ts, dh))
            if not cands:
                break
            best = cands[0]
            selected.remove(worst)
            selected_ids.discard(worst['id'])
            selected.append(best)
            selected_ids.add(best['id'])
            *_, ga_now = coverage_of(selected)

    # 3.6b: influencing 单独补足（题库839题最少，需保证至少20题）
    while True:
        *_, ga_now = coverage_of(selected)
        if ga_now.get('influencing', 0) >= MIN_GALLUP_INFLUENCING:
            break
        # 找含influencing、未选入的题
        cands = [
            it for it in bank
            if it['id'] not in selected_ids
            and 'influencing' in gallup_domain_count_in_item(it)
            and not any(_is_near_duplicate(sel['stem'], it['stem']) for sel in selected)
        ]
        cands.sort(key=lambda it: -state_match_score(it, ts, dh))
        if not cands:
            break
        best = cands[0]
        # 找可替换的题：不含influencing的，优先strategic_thinking（之前已经过载）
        replaceable = [
            it for it in selected
            if 'influencing' not in gallup_domain_count_in_item(it)
            and not _gallup_protected(it)
        ]
        if not replaceable:
            break
        # 优先替换含strategic_thinking的题（平衡4领域）
        replaceable.sort(key=lambda it: (
            'strategic_thinking' not in gallup_domain_count_in_item(it),  # strategic_thinking题优先替换
            state_match_score(it, ts, dh)  # 状态分低的优先替换
        ))
        worst = replaceable[0]
        selected.remove(worst)
        selected_ids.discard(worst['id'])
        selected.append(best)
        selected_ids.add(best['id'])

    # Step 4: 量表多样性补足 —— 确保新量表类型(likert-5/likert-7/ranking)进入试卷
    # （放在reverse之前，避免reverse步骤把新量表题挤掉）
    for scale_type, min_count in MIN_SCALE_DIVERSITY.items():
        current = sum(1 for it in selected if it.get('scale') == scale_type)
        while current < min_count:
            cands = [
                it for it in bank
                if it['id'] not in selected_ids
                and it.get('scale') == scale_type
            ]
            cands.sort(key=lambda it: -state_match_score(it, ts, dh))
            if not cands:
                break
            best = cands[0]
            is_dup = any(_is_near_duplicate(sel['stem'], best['stem']) for sel in selected)
            if is_dup:
                # 尝试下一个候选
                found = False
                for c in cands[1:]:
                    is_dup2 = any(_is_near_duplicate(sel['stem'], c['stem']) for sel in selected)
                    if not is_dup2:
                        best = c
                        found = True
                        break
                if not found:
                    break
            # 从forced-choice中找可替换的（forced-choice占最多），但不替换reverse题
            cat_count_now = Counter(it['category'] for it in selected)
            replaceable = [
                it for it in selected
                if it.get('scale') == 'forced-choice'
                and not it.get('reverse')
                and cat_count_now[it['category']] > 8
            ]
            if not replaceable:
                # 尝试替换likert-4（非reverse）
                replaceable = [
                    it for it in selected
                    if it.get('scale') == 'likert-4'
                    and not it.get('reverse')
                    and cat_count_now[it['category']] > 8
                ]
            if not replaceable:
                break
            worst = min(replaceable, key=lambda it: state_match_score(it, ts, dh))
            selected.remove(worst)
            selected_ids.discard(worst['id'])
            selected.append(best)
            selected_ids.add(best['id'])
            current += 1

    # Step 4.5: reverse 题补足
    rev_count = sum(1 for it in selected if it.get('reverse'))
    if rev_count < MIN_REVERSE:
        cands = [it for it in bank if it.get('reverse') and it['id'] not in selected_ids]
        cands.sort(key=lambda it: -state_match_score(it, ts, dh))
        for c in cands:
            if sum(1 for it in selected if it.get('reverse')) >= MIN_REVERSE:
                break
            # 去重检查
            is_dup = any(_is_near_duplicate(sel['stem'], c['stem']) for sel in selected)
            if is_dup:
                continue
            # 从非reverse题中找可替换的（优先替换状态分最低的）
            cat_count_now = Counter(it['category'] for it in selected)
            replaceable = [
                it for it in selected
                if not it.get('reverse')
                and cat_count_now[it['category']] > 8
            ]
            if not replaceable:
                # 回退：允许从最低类别的题中替换
                replaceable = [it for it in selected if not it.get('reverse')]
            worst = min(replaceable, key=lambda it: state_match_score(it, ts, dh), default=None)
            if worst is None:
                break
            selected.remove(worst)
            selected_ids.discard(worst['id'])
            selected.append(c)
            selected_ids.add(c['id'])

    # Step 4.5: 最终去重保障 — 清除所有步骤可能引入的残留重复
    final_dedup = 0
    i = 0
    while i < len(selected):
        j = i + 1
        while j < len(selected):
            if _is_near_duplicate(selected[i]['stem'], selected[j]['stem']):
                # 保留 state_match_score 更高的
                if state_match_score(selected[i], ts) >= state_match_score(selected[j], ts):
                    worse = selected[j]
                else:
                    worse = selected[i]
                selected_ids.discard(worse['id'])
                selected.remove(worse)
                final_dedup += 1
                # 找替代题（检查类别不超限）
                replacement = None
                cat_count_now = Counter(sel['category'] for sel in selected)
                for s, it in sorted(scored, key=lambda x: -x[0]):
                    if it['id'] not in selected_ids and it['id'] != worse['id']:
                        if cat_count_now.get(it['category'], 0) >= 15:
                            continue
                        is_dup = any(_is_near_duplicate(sel['stem'], it['stem']) for sel in selected)
                        if not is_dup:
                            replacement = it
                            break
                if replacement:
                    selected.append(replacement)
                    selected_ids.add(replacement['id'])
                # 不递增 j
            else:
                j += 1
        i += 1

    # Step 4.7: 类别均衡 —— 每类限制在 8~15 题之间
    CAT_MIN = 8
    CAT_MAX = 15

    def _is_protected(it):
        """判断题目是否受保护（不应被后续步骤移除）"""
        # reverse题在达标线时不移除
        if it.get('reverse'):
            rev_now = sum(1 for s in selected if s.get('reverse'))
            if rev_now <= MIN_REVERSE:
                return True
        # 新量表类型在达标线时不移除
        scale = it.get('scale', '')
        if scale in ('likert-5', 'likert-7', 'ranking'):
            sc_now = sum(1 for s in selected if s.get('scale') == scale)
            if sc_now <= MIN_SCALE_DIVERSITY.get(scale, 0):
                return True
        return False

    while True:
        cat_counts = Counter(it['category'] for it in selected)
        over_cats = [c for c, n in cat_counts.items() if n > CAT_MAX]
        under_cats = [c for c in CATEGORIES if cat_counts.get(c, 0) < CAT_MIN]
        if not over_cats or not under_cats:
            break
        # 计算当前gallup领域分布，用于在类别均衡时保持领域平衡
        *_, ga_current = coverage_of(selected)
        over_domains = {d for d in GALLUP_DOMAINS if ga_current.get(d, 0) > MAX_GALLUP_PER_DOMAIN}
        swapped = False
        for over_cat in over_cats:
            # 优先替换含过载gallup领域的题
            over_qs = sorted(
                [it for it in selected if it['category'] == over_cat and not _is_protected(it)],
                key=lambda it: (
                    -len(gallup_domain_count_in_item(it) & over_domains),  # 含过载领域越多越优先替换
                    state_match_score(it, ts)
                )
            )
            for q_over in over_qs:
                if cat_counts.get(over_cat, 0) <= CAT_MAX:
                    break
                found_replacement = False
                for under_cat in under_cats:
                    if cat_counts.get(under_cat, 0) >= CAT_MIN:
                        continue
                    cands = [
                        it for it in bank
                        if it['id'] not in selected_ids
                        and it['category'] == under_cat
                    ]
                    # 排序：优先选不含过载领域的候选题，状态分高的优先
                    cands.sort(key=lambda it: (
                        len(gallup_domain_count_in_item(it) & over_domains),  # 含过载领域越少越优先
                        -state_match_score(it, ts)
                    ))
                    for c in cands:
                        is_dup = any(_is_near_duplicate(sel['stem'], c['stem']) for sel in selected)
                        if not is_dup:
                            selected.remove(q_over)
                            selected_ids.discard(q_over['id'])
                            selected.append(c)
                            selected_ids.add(c['id'])
                            cat_counts[over_cat] -= 1
                            cat_counts[under_cat] = cat_counts.get(under_cat, 0) + 1
                            swapped = True
                            found_replacement = True
                            break
                    if found_replacement:
                        break
        if not swapped:
            break

    # Step 5: 难度分布校准 —— 向目标 {2:36, 3:54, 4:24, 5:6} 靠拢
    DIFF_TARGET = {2: 36, 3: 54, 4: 24, 5: 6}  # 难度1不进卷

    # 5a: 替换难度1的题（同时检查类别不超限，保护reverse和新量表题）
    diff1_qs = [it for it in selected if it.get('difficulty', 0) == 1 and not _is_protected(it)]
    for q1 in diff1_qs:
        cands = [
            it for it in bank
            if it['id'] not in selected_ids
            and it.get('difficulty', 0) in (2, 3)
        ]
        cands.sort(key=lambda it: (-state_match_score(it, ts), it.get('difficulty', 0)))
        cat_count_now = Counter(sel['category'] for sel in selected)
        for c in cands:
            if cat_count_now.get(c['category'], 0) >= 15:
                continue
            is_dup = any(_is_near_duplicate(sel['stem'], c['stem']) for sel in selected)
            if not is_dup:
                selected.remove(q1)
                selected_ids.discard(q1['id'])
                selected.append(c)
                selected_ids.add(c['id'])
                break

    # 5b: 校准难度2-5的分布（同时检查类别不超限）
    for _ in range(3):
        diff_dist = Counter(it.get('difficulty', 0) for it in selected)
        for d in [2, 3, 4, 5]:
            current = diff_dist.get(d, 0)
            target = DIFF_TARGET[d]
            if current <= target:
                continue
            over_qs = sorted(
                [it for it in selected if it.get('difficulty', 0) == d and not _is_protected(it)],
                key=lambda it: state_match_score(it, ts)
            )
            for q_over in over_qs:
                if diff_dist.get(d, 0) <= target:
                    break
                found_replacement = False
                for d_under in [2, 3, 4, 5]:
                    if diff_dist.get(d_under, 0) >= DIFF_TARGET[d_under]:
                        continue
                    cands = [
                        it for it in bank
                        if it['id'] not in selected_ids
                        and it.get('difficulty', 0) == d_under
                    ]
                    cands.sort(key=lambda it: -state_match_score(it, ts))
                    cat_count_now = Counter(sel['category'] for sel in selected)
                    for c in cands:
                        if cat_count_now.get(c['category'], 0) >= 15:
                            continue
                        is_dup = any(_is_near_duplicate(sel['stem'], c['stem']) for sel in selected)
                        if not is_dup:
                            selected.remove(q_over)
                            selected_ids.discard(q_over['id'])
                            selected.append(c)
                            selected_ids.add(c['id'])
                            diff_dist[d] -= 1
                            diff_dist[d_under] = diff_dist.get(d_under, 0) + 1
                            found_replacement = True
                            break
                    if found_replacement:
                        break

    # Step 5.5: 最终盖洛普4领域平衡 —— 多轮修正，确保所有步骤完成后4领域不超MAX
    # 单轮处理时修复A可能把B推过MAX，所以循环到稳定
    for _round in range(5):
        changed = False
        for over_domain in GALLUP_DOMAINS:
            *_, ga_now = coverage_of(selected)
            safety = 0
            while ga_now.get(over_domain, 0) > MAX_GALLUP_PER_DOMAIN and safety < 40:
                safety += 1
                replaceable = [
                    it for it in selected
                    if over_domain in gallup_domain_count_in_item(it)
                    and not it.get('reverse')
                ]
                if not replaceable:
                    break
                replaceable.sort(key=lambda it: (
                    state_match_score(it, ts, dh),
                    -len(gallup_domain_count_in_item(it) - {over_domain})
                ))
                worst = replaceable[0]
                # 候选：不含over_domain；优先选不会把其他领域推过MAX的题
                cands = [
                    it for it in bank
                    if it['id'] not in selected_ids
                    and over_domain not in gallup_domain_count_in_item(it)
                    and any(k.startswith('gallup.') for o in it['options'] for k in o.get('score', {}))
                    and not any(_is_near_duplicate(sel['stem'], it['stem']) for sel in selected)
                ]
                # 排序：① 不含其他已过载领域优先 ② 状态分高优先
                cands.sort(key=lambda it: (
                    sum(1 for d in GALLUP_DOMAINS if d != over_domain and d in gallup_domain_count_in_item(it) and ga_now.get(d, 0) >= MAX_GALLUP_PER_DOMAIN),
                    -state_match_score(it, ts, dh)
                ))
                if not cands:
                    break
                best = cands[0]
                selected.remove(worst)
                selected_ids.discard(worst['id'])
                selected.append(best)
                selected_ids.add(best['id'])
                *_, ga_now = coverage_of(selected)
                changed = True
        if not changed:
            break

    # Step 6: 排序 —— 类别交错 + 难度递增
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
        'scale_dist': dict(sorted(Counter(it.get('scale', 'unknown') for it in ordered).items())),
        'multi_system_count': sum(1 for it in ordered if len(set(k.split('.')[0] for o in it['options'] for k in o.get('score', {}))) >= 4),
    }
    # 达标检查
    checks = {
        'enneagram_all_types>=5': all(v >= MIN_ENNEAGRAM_PER_TYPE for v in report['enneagram'].values()),
        'mbti_all_poles>=4': all(v >= MIN_MBTI_PER_POLE for v in report['mbti'].values()),
        'holland_all_types>=2(R>=2)': all(ho.get(t, 0) >= (MIN_HOLLAND_R if t == 'R' else MIN_HOLLAND_PER_TYPE) for t in 'RIASEC'),
        'gallup_all_domains>=8': all(v >= MIN_GALLUP_PER_DOMAIN for v in report['gallup'].values()),
        'reverse>=10': report['reverse_count'] >= MIN_REVERSE,
        'scale_diversity_ok': all(
            report['scale_dist'].get(st, 0) >= mc
            for st, mc in MIN_SCALE_DIVERSITY.items()
        ),
        'holland_questions>=30': sum(1 for it in ordered if any(k.startswith('holland.') for o in it['options'] for k in o.get('score', {}))) >= MIN_HOLLAND_QUESTIONS,
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
