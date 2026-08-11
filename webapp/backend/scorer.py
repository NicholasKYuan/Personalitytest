#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scorer.py — 四体系评分逻辑
接收100题答案，计算九型人格 / MBTI / 霍兰德 / 盖洛普结果。
"""
from collections import Counter, defaultdict

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
    gallup_themes_counter = Counter()

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

        # 统计盖洛普主题频次
        for theme in q.get("gallup_themes", []):
            gallup_themes_counter[theme] += 1

    # === 九型人格：取最高分为主型 ===
    enneagram_result = {}
    for i in range(1, 10):
        enneagram_result[f"type{i}"] = enneagram_scores.get(f"type{i}", 0)

    type_keys = [f"type{i}" for i in range(1, 10)]
    main_type_key = max(type_keys, key=lambda k: enneagram_result[k])
    main_type_num = int(main_type_key.replace("type", ""))
    main_type_name = ENNEAGRAM_NAMES[main_type_num]

    # === MBTI：四对取高者 ===
    mbti_pairs = [("E", "I"), ("S", "N"), ("T", "F"), ("J", "P")]
    mbti_type = ""
    for a, b in mbti_pairs:
        if mbti_scores.get(a, 0) >= mbti_scores.get(b, 0):
            mbti_type += a
        else:
            mbti_type += b

    mbti_dimensions = {p: mbti_scores.get(p, 0) for p in "EISNTFJP"}

    # === 霍兰德：取前3高分组成代码 ===
    holland_all = {t: holland_scores.get(t, 0) for t in "RIASEC"}
    holland_sorted = sorted(holland_all.items(), key=lambda x: (-x[1], x[0]))
    holland_code = "".join(t for t, _ in holland_sorted[:3])

    # === 盖洛普：4领域分值排序 + top5主题 ===
    gallup_domains = {
        d: gallup_domain_scores.get(d, 0)
        for d in ["executing", "influencing", "relationship_building", "strategic_thinking"]
    }
    top_domain = max(gallup_domains, key=gallup_domains.get)
    top_themes = [t for t, _ in gallup_themes_counter.most_common(5)]

    return {
        "enneagram": {
            "main_type": main_type_num,
            "type_name": main_type_name,
            "scores": enneagram_result,
        },
        "mbti": {
            "type": mbti_type,
            "dimensions": mbti_dimensions,
        },
        "holland": {
            "code": holland_code,
            "scores": holland_all,
        },
        "gallup": {
            "top_domain": top_domain,
            "domains": gallup_domains,
            "top_themes": top_themes,
        },
    }


def generate_free_summary(results, profile):
    """
    根据四体系结果生成免费简评。
    """
    name = profile.get("name", "你")
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
