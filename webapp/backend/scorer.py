#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scorer.py — 四体系评分逻辑
接收100题答案，计算九型人格 / MBTI / 霍兰德 / 盖洛普结果。

评分规范:
1. 盖洛普主题按"选项领域得分加权"计分: 对每道已答题, 用户所选选项中
   gallup.<domain> 的分值 v (v>0), 累加到该题 gallup_themes 中属于该
   domain 的每个主题上; top_themes 取权重>0 的前5 (权重降序, 主题名升序)。
2. 判型使用归一化分数: normalized[key] = raw[key] / max_attainable[key],
   其中 max_attainable[key] = 本卷每道已答题各选项中该 key 最大分值之和,
   消除题库维度覆盖不均带来的系统性偏移。raw 分数字段保持不变, 各体系
   结果 dict 中新增 "normalized" 子字典 (保留3位小数)。
"""
from collections import defaultdict

# 九型人格类型名称映射
ENNEAGRAM_NAMES = {
    1: "完美主义者",
    2: "助人者",
    3: "成就者",
    4: "个人主义者",
    5: "观察者",
    6: "忠诚者",
    7: "热情者",
    8: "挑战者",
    9: "和平者",
}

# 盖洛普四领域的中文名称
GALLUP_DOMAIN_NAMES = {
    "executing": "执行力",
    "influencing": "影响力",
    "relationship_building": "关系建立",
    "strategic_thinking": "战略思维",
}

# 盖洛普 34 主题的中文名称
GALLUP_THEME_NAMES = {
    "achiever": "成就", "activator": "行动", "adaptability": "适应",
    "analytical": "分析", "arranger": "统筹", "belief": "信仰",
    "command": "统率", "communication": "沟通", "competition": "竞争",
    "connectedness": "关联", "context": "回顾", "consistency": "公平",
    "deliberative": "审慎", "developer": "伯乐", "discipline": "纪律",
    "empathy": "体谅", "focus": "专注", "futuristic": "前瞻",
    "harmony": "和谐", "ideation": "理念", "includer": "包容",
    "individualization": "个别", "input": "搜集", "intellection": "思维",
    "learner": "学习", "maximizer": "完美", "positivity": "积极",
    "relator": "交往", "responsibility": "责任", "restorative": "排难",
    "self_assurance": "自信", "significance": "追求", "strategic": "战略",
    "woo": "取悦",
}

# CliftonStrengths 官方 34 主题 -> 四领域映射
GALLUP_DOMAIN_THEMES = {
    "executing": [
        "achiever", "arranger", "belief", "consistency", "deliberative",
        "discipline", "focus", "responsibility", "restorative",
    ],
    "influencing": [
        "activator", "command", "communication", "competition",
        "maximizer", "self_assurance", "significance", "woo",
    ],
    "relationship_building": [
        "adaptability", "connectedness", "developer", "empathy", "harmony",
        "includer", "individualization", "positivity", "relator",
    ],
    "strategic_thinking": [
        "analytical", "context", "futuristic", "ideation", "input",
        "intellection", "learner", "strategic",
    ],
}

GALLUP_THEME_TO_DOMAIN = {
    theme: domain
    for domain, themes in GALLUP_DOMAIN_THEMES.items()
    for theme in themes
}


# 旧版/非官方主题名 -> 官方 34 主题名
GALLUP_THEME_ALIASES = {
    "compliance": "consistency",          # 2015 年前官方旧名
    "individuality": "individualization",
    "fixer": "restorative",
}


def _normalize_theme_name(theme):
    """题库中主题名可能用连字符 (self-assurance) 或旧版别名, 统一归一为官方下划线形式。"""
    t = theme.replace("-", "_")
    return GALLUP_THEME_ALIASES.get(t, t)


def score_answers(questions, answers):
    """
    计算100题答案的四体系结果。

    Args:
        questions: 100道题的完整数据（含 options[].score）
        answers: [{"question_id": "Q0001", "option_index": 0}, ...]

    Returns:
        {
            "enneagram": {"main_type": 3, "type_name": "成就者", "scores": {"type1": x, ...}},
            "mbti": {"type": "ENTJ", "dimensions": {"E": x, "I": x, ...}},
            "holland": {"code": "EAS", "scores": {"R": x, "I": x, ...}},
            "gallup": {"top_domain": "executing", "domains": {...}, "top_themes": [...]}
        }
    """
    # 构建 question_id -> question 的索引
    q_map = {q["id"]: q for q in questions}

    # 累加各维度分值
    enneagram_scores = defaultdict(int)  # type1-type9
    mbti_scores = defaultdict(int)       # E, I, S, N, T, F, J, P
    holland_scores = defaultdict(int)    # R, I, A, S, E, C
    gallup_domain_scores = defaultdict(int)  # executing, influencing, relationship_building, strategic_thinking
    gallup_theme_weights = defaultdict(int)  # 主题 -> 加权得分
    max_attainable = defaultdict(int)    # 维度 key -> 本卷最大可得分

    for ans in answers:
        qid = ans["question_id"]
        opt_idx = ans["option_index"]
        q = q_map.get(qid)
        if q is None:
            continue
        if opt_idx < 0 or opt_idx >= len(q["options"]):
            continue

        option = q["options"][opt_idx]
        score = option.get("score", {})

        # 该题各维度的最大可得分 (跨所有选项取最大后累加)
        q_dim_keys = set()
        for opt in q["options"]:
            q_dim_keys.update(opt.get("score", {}).keys())
        for dim_key in q_dim_keys:
            max_attainable[dim_key] += max(
                opt.get("score", {}).get(dim_key, 0) for opt in q["options"]
            )

        # 该题的盖洛普主题 (归一化连字符)
        q_themes = [_normalize_theme_name(t) for t in q.get("gallup_themes", [])]

        for dim_key, val in score.items():
            parts = dim_key.split(".")
            if len(parts) != 2:
                continue
            system, sub = parts[0], parts[1]

            if system == "enneagram":
                enneagram_scores[sub] += val
            elif system == "mbti":
                mbti_scores[sub] += val
            elif system == "holland":
                holland_scores[sub] += val
            elif system == "gallup":
                gallup_domain_scores[sub] += val
                # 盖洛普主题加权: 所选选项在该领域得分 v>0 时,
                # 该题主题中属于该领域的每个主题累加 v
                if val > 0:
                    for theme in q_themes:
                        if GALLUP_THEME_TO_DOMAIN.get(theme) == sub:
                            gallup_theme_weights[theme] += val

    def _normalized_exact(prefix, sub_keys):
        """按 raw / max_attainable 计算归一化分数 (未舍入, 用于判型比较)。"""
        raw_map = {
            "enneagram": enneagram_scores,
            "mbti": mbti_scores,
            "holland": holland_scores,
            "gallup": gallup_domain_scores,
        }[prefix]
        result = {}
        for sub in sub_keys:
            cap = max_attainable.get(f"{prefix}.{sub}", 0)
            result[sub] = raw_map.get(sub, 0) / cap if cap > 0 else 0.0
        return result

    def _rounded(norm_map):
        """展示用副本 (保留3位小数); 判型一律用未舍入值。"""
        return {k: round(v, 3) for k, v in norm_map.items()}

    # === 九型人格：归一化最高分为主型, 平手取型号小的 ===
    enneagram_result = {}
    for i in range(1, 10):
        enneagram_result[f"type{i}"] = enneagram_scores.get(f"type{i}", 0)

    enneagram_exact = _normalized_exact("enneagram", [f"type{i}" for i in range(1, 10)])
    main_type_num = min(range(1, 10), key=lambda i: (-enneagram_exact[f"type{i}"], i))
    main_type_name = ENNEAGRAM_NAMES[main_type_num]
    enneagram_normalized = _rounded(enneagram_exact)

    # === MBTI：四对按归一化取高者, >= 取前者 (E/S/T/J 优先) ===
    mbti_exact = _normalized_exact("mbti", list("EISNTFJP"))
    mbti_pairs = [("E", "I"), ("S", "N"), ("T", "F"), ("J", "P")]
    mbti_type = ""
    for a, b in mbti_pairs:
        if mbti_exact[a] >= mbti_exact[b]:
            mbti_type += a
        else:
            mbti_type += b
    mbti_normalized = _rounded(mbti_exact)

    mbti_dimensions = {p: mbti_scores.get(p, 0) for p in "EISNTFJP"}

    # === 霍兰德：归一化前3组成代码, 平手按字母序 ===
    holland_all = {t: holland_scores.get(t, 0) for t in "RIASEC"}
    holland_exact = _normalized_exact("holland", list("RIASEC"))
    holland_sorted = sorted(holland_exact.items(), key=lambda x: (-x[1], x[0]))
    holland_code = "".join(t for t, _ in holland_sorted[:3])
    holland_normalized = _rounded(holland_exact)

    # === 盖洛普：主导领域按归一化判定 (平手按领域名字母序), 加权 top5 主题 ===
    gallup_domain_keys = ["executing", "influencing", "relationship_building", "strategic_thinking"]
    gallup_domains = {d: gallup_domain_scores.get(d, 0) for d in gallup_domain_keys}
    gallup_exact = _normalized_exact("gallup", gallup_domain_keys)
    top_domain = min(gallup_domain_keys, key=lambda d: (-gallup_exact[d], d))
    gallup_normalized = _rounded(gallup_exact)
    top_themes = [
        t for t, w in sorted(gallup_theme_weights.items(), key=lambda x: (-x[1], x[0]))
        if w > 0
    ][:5]

    return {
        "enneagram": {
            "main_type": main_type_num,
            "type_name": main_type_name,
            "scores": enneagram_result,
            "normalized": enneagram_normalized,
        },
        "mbti": {
            "type": mbti_type,
            "dimensions": mbti_dimensions,
            "normalized": mbti_normalized,
        },
        "holland": {
            "code": holland_code,
            "scores": holland_all,
            "normalized": holland_normalized,
        },
        "gallup": {
            "top_domain": top_domain,
            "domains": gallup_domains,
            "top_themes": top_themes,
            "normalized": gallup_normalized,
        },
    }


def generate_free_summary(results, profile):
    """
    根据四体系结果生成免费简评。
    """
    name = profile.get("name") or "你"
    enneagram = results["enneagram"]
    mbti = results["mbti"]
    holland = results["holland"]
    gallup = results["gallup"]

    summary_parts = [
        f"{name}的九型人格主型为【{enneagram['main_type']}号 - {enneagram['type_name']}】。",
        f"MBTI类型为【{mbti['type']}】。",
        f"霍兰德职业兴趣代码为【{holland['code']}】。",
        f"盖洛普优势主导领域为【{GALLUP_DOMAIN_NAMES.get(gallup['top_domain'], gallup['top_domain'])}】。",
    ]

    if gallup["top_themes"]:
        themes_cn = [GALLUP_THEME_NAMES.get(t, t) for t in gallup["top_themes"][:3]]
        themes_str = "、".join(themes_cn)
        summary_parts.append(f"核心优势主题包括：{themes_str}。")

    summary_parts.append("解锁深度报告，获取四体系交叉解读与AI个性化建议。")

    return " ".join(summary_parts)
