#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
report_generator.py — 填充详细报告模板，生成可下载的 HTML 报告。
接收评分结果 + AI 分析章节，填充 report-detailed.html 模板。
"""
import json
import math
from pathlib import Path
from datetime import datetime

BACKEND_DIR = Path(__file__).parent.resolve()
TEMPLATE_DIR = BACKEND_DIR.parent / "templates"

# 角色与目的中文映射
ROLE_CN = {
    "student-junior-high": "初中生", "student-senior-high": "高中生",
    "student-undergrad": "本科生", "student-grad": "硕士生",
    "student-phd": "博士生", "employed": "在职人士",
    "freelancer": "自由职业者", "entrepreneur": "创业者",
    "parent": "家长", "job-seeker": "求职者",
}

PURPOSE_CN = {
    "career-planning": "职业规划", "study-direction": "学习方向选择",
    "study-abroad-planning": "留学规划", "graduate-school-planning": "考研/保研规划",
    "self-exploration": "自我探索", "relationship-insight": "人际关系洞察",
    "leadership-growth": "领导力成长", "entrepreneur-fit": "创业适配评估",
    "academic-stress-relief": "学业压力舒缓", "parent-understanding-child": "了解孩子",
}

# 霍兰德代码中文描述
HOLLAND_LABELS = {
    "R": "实际型", "I": "研究型", "A": "艺术型",
    "S": "社会型", "E": "企业型", "C": "常规型",
}

# MBTI 类型简述
MBTI_LABELS = {
    "INTJ": "建筑师", "INTP": "逻辑学家", "ENTJ": "指挥官", "ENTP": "辩论家",
    "INFJ": "提倡者", "INFP": "调停者", "ENFJ": "主人公", "ENFP": "竞选者",
    "ISTJ": "物流师", "ISFJ": "守卫者", "ESTJ": "总经理", "ESFJ": "执政官",
    "ISTP": "鉴赏家", "ISFP": "探险家", "ESTP": "企业家", "ESFP": "表演者",
}

# 盖洛普领域中文名
GALLUP_DOMAIN_CN = {
    "executing": "执行力", "influencing": "影响力",
    "relationship_building": "关系建立", "strategic_thinking": "战略思维",
}

GALLUP_THEME_CN = {
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


def _pct(score, max_score):
    """计算百分比，最小 5%"""
    if max_score == 0:
        return 5
    return max(5, min(100, round(score / max_score * 100)))


def _radar_points(results):
    """计算雷达图 SVG 坐标点"""
    en = results.get("enneagram", {})
    mb = results.get("mbti", {})
    ho = results.get("holland", {})
    ga = results.get("gallup", {})

    # 各体系最高分
    en_max = max(en.get("scores", {}).values()) if en.get("scores") else 1
    mb_scores = mb.get("dimensions", {})
    mb_max = max(mb_scores.values()) if mb_scores else 1
    ho_scores = ho.get("scores", {})
    ho_max = max(ho_scores.values()) if ho_scores else 1
    ga_scores = ga.get("domains", {})
    ga_max = max(ga_scores.values()) if ga_scores else 1

    # 综合分 = 四体系平均归一化
    composite = (en_max + mb_max + ho_max + ga_max) / 4

    # 归一化到 0-1
    vals = [en_max, mb_max, ho_max, ga_max, composite]
    all_max = max(vals) if vals else 1
    normalized = [v / all_max if all_max > 0 else 0 for v in vals]

    # 雷达图五个顶点坐标 (正五边形)
    cx, cy = 150, 150
    radius = 120
    angles = [-90, -90 + 72, -90 + 144, -90 + 216, -90 + 288]
    import math
    points = []
    for i, angle in enumerate(angles):
        rad = math.radians(angle)
        r = radius * normalized[i]
        x = cx + r * math.cos(rad)
        y = cy + r * math.sin(rad)
        points.append(f"{x:.1f},{y:.1f}")

    return " ".join(points)


def _markdown_to_html(md):
    """简易 Markdown 转 HTML"""
    if not md:
        return ""
    import re
    # 转义
    md = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    lines = md.split("\n")
    html_parts = []
    in_ul = False
    in_ol = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            continue

        # 标题
        m = re.match(r'^(#{2,3})\s+(.+)', stripped)
        if m:
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            level = len(m.group(1))
            html_parts.append(f"<h{level}>{m.group(2)}</h{level}>")
            continue

        # 无序列表
        m = re.match(r'^-\s+(.+)', stripped)
        if m:
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            html_parts.append(f"<li>{m.group(1)}</li>")
            continue

        # 有序列表
        m = re.match(r'^\d+[\.\)]\s+(.+)', stripped)
        if m:
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            html_parts.append(f"<li>{m.group(1)}</li>")
            continue

        # 段落
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False
        # 加粗
        text = stripped.replace("**", "</strong>", 1) if "**" in stripped else stripped
        text = text.replace("**", "<strong>", 1) if "**" in text else text
        html_parts.append(f"<p>{text}</p>")

    if in_ul:
        html_parts.append("</ul>")
    if in_ol:
        html_parts.append("</ol>")

    return "\n".join(html_parts)


def _extract_section(sections, keywords):
    """从 AI sections 中按关键词提取内容"""
    for s in sections:
        title = s.get("title", "")
        for kw in keywords:
            if kw in title:
                return _markdown_to_html(s.get("content", ""))
    return ""


def generate_report_html(results, profile, ai_sections):
    """
    生成完整的 HTML 报告。

    Args:
        results: score_answers() 的返回值
        profile: 用户信息 dict
        ai_sections: AI 生成的章节列表 [{"title": "...", "content": "..."}]

    Returns:
        str: 完整的 HTML 字符串
    """
    template_path = TEMPLATE_DIR / "report-detailed.html"
    html = template_path.read_text(encoding="utf-8")

    # --- 基础信息 ---
    name = profile.get("name", "用户")
    age = profile.get("age", "")
    role_cn = ROLE_CN.get(profile.get("role", ""), profile.get("role", ""))
    purpose_cn = PURPOSE_CN.get(profile.get("purpose", ""), profile.get("purpose", ""))
    report_date = datetime.now().strftime("%Y年%m月%d日")
    birth_date = profile.get("birth_date", "")

    # --- 九型人格 ---
    en = results.get("enneagram", {})
    en_scores = en.get("scores", {})
    en_max = max(en_scores.values()) if en_scores else 1

    # --- MBTI ---
    mb = results.get("mbti", {})
    mb_dims = mb.get("dimensions", {})
    mb_max = max(mb_dims.values()) if mb_dims else 1

    # --- 霍兰德 ---
    ho = results.get("holland", {})
    ho_scores = ho.get("scores", {})
    ho_max = max(ho_scores.values()) if ho_scores else 1
    holland_code = ho.get("code", "")
    holland_label = "、".join(HOLLAND_LABELS.get(c, c) for c in holland_code)

    # --- 盖洛普 ---
    ga = results.get("gallup", {})
    ga_domains = ga.get("domains", {})
    ga_max = max(ga_domains.values()) if ga_domains else 1
    ga_themes = ga.get("top_themes", [])[:5]
    ga_domain_cn = GALLUP_DOMAIN_CN.get(ga.get("top_domain", ""), ga.get("top_domain", ""))

    # 主题标签 HTML
    theme_tags = "".join(
        f'<span class="theme-tag">{GALLUP_THEME_CN.get(t, t)}</span>'
        for t in ga_themes
    )

    # 职业推荐列表
    career_suggestions = _extract_section(ai_sections, ["霍兰德", "职业", "方向"])
    career_list_html = ""
    if career_suggestions:
        career_list_html = f"<li>{career_suggestions}</li>"
    else:
        career_list_html = "<li>请参考霍兰德代码对应的职业方向</li>"

    # AI 章节内容
    enneagram_analysis = _extract_section(ai_sections, ["九型", "enneagram"])
    mbti_analysis = _extract_section(ai_sections, ["MBTI", "mbti"])
    holland_analysis = _extract_section(ai_sections, ["霍兰德", "holland", "职业"])
    gallup_analysis = _extract_section(ai_sections, ["盖洛普", "gallup", "优势"])
    cross_analysis = _extract_section(ai_sections, ["交叉", "综合", "cross"])

    # 易学章节
    lifecycle_content = ""
    if birth_date:
        lifecycle_content = _extract_section(ai_sections, ["易学", "传统", "命理", "生涯", "lifecycle"])

    # 协同点与张力点
    synergy = _extract_section(ai_sections, ["协同", "synergy"])
    tension = _extract_section(ai_sections, ["张力", "tension"])
    if not synergy:
        synergy = "详见综合交叉解读"
    if not tension:
        tension = "详见综合交叉解读"

    # MBTI 标签
    mbti_type = mb.get("type", "")
    mbti_label = MBTI_LABELS.get(mbti_type, "")

    # 替换占位符
    replacements = {
        "{{USER_NAME}}": name,
        "{{USER_AGE}}": str(age),
        "{{USER_ROLE_CN}}": role_cn,
        "{{USER_PURPOSE_CN}}": purpose_cn,
        "{{REPORT_DATE}}": report_date,
        "{{BIRTH_DATE}}": birth_date,

        "{{ENNEAGRAM_TYPE}}": str(en.get("main_type", "")),
        "{{ENNEAGRAM_NAME}}": en.get("type_name", ""),

        "{{MBTI_TYPE}}": mbti_type,
        "{{MBTI_LABEL}}": mbti_label,

        "{{HOLLAND_CODE}}": holland_code,
        "{{HOLLAND_LABEL}}": holland_label,

        "{{GALLUP_DOMAIN_CN}}": ga_domain_cn,
        "{{RADAR_POINTS}}": _radar_points(results),

        "{{CAREER_LIST}}": career_list_html,
        "{{GALLUP_THEME_TAGS}}": theme_tags,

        "{{ENNEAGRAM_ANALYSIS}}": enneagram_analysis,
        "{{MBTI_ANALYSIS}}": mbti_analysis,
        "{{HOLLAND_ANALYSIS}}": holland_analysis,
        "{{GALLUP_ANALYSIS}}": gallup_analysis,
        "{{CROSS_ANALYSIS}}": cross_analysis,
        "{{SYNERGY_POINTS}}": synergy,
        "{{TENSION_POINTS}}": tension,

        "{{LIFECYCLE_CURRENT}}": lifecycle_content if lifecycle_content else "",
        "{{LIFECYCLE_FOCUS}}": "",
        "{{LIFECYCLE_PITFALL}}": "",
        "{{LIFECYCLE_CROSS}}": "",
    }

    # 九型得分
    for i in range(1, 10):
        score = en_scores.get(f"type{i}", 0)
        replacements[f"{{{{ENNEAGRAM_SCORE_{i}}}}}"] = str(score)
        replacements[f"{{{{ENNEAGRAM_PCT_{i}}}}}"] = str(_pct(score, en_max))

    # MBTI 得分
    for dim in "EISNTFJP":
        score = mb_dims.get(dim, 0)
        replacements[f"{{{{MBTI_SCORE_{dim}}}}}"] = str(score)
        replacements[f"{{{{MBTI_PCT_{dim}}}}}"] = str(_pct(score, mb_max))

    # 霍兰德得分
    for t in "RIASEC":
        score = ho_scores.get(t, 0)
        replacements[f"{{{{HOLLAND_SCORE_{t}}}}}"] = str(score)
        replacements[f"{{{{HOLLAND_PCT_{t}}}}}"] = str(_pct(score, ho_max))

    # 盖洛普得分
    for key, dim in [("EXEC", "executing"), ("INFL", "influencing"),
                      ("REL", "relationship_building"), ("STRAT", "strategic_thinking")]:
        score = ga_domains.get(dim, 0)
        replacements[f"{{{{GALLUP_SCORE_{key}}}}}"] = str(score)
        replacements[f"{{{{GALLUP_PCT_{key}}}}}"] = str(_pct(score, ga_max))

    # 执行替换
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    # 处理条件块 {{IF_LIFECYCLE}} ... {{/IF_LIFECYCLE}}
    if birth_date:
        html = html.replace("<!-- {{IF_LIFECYCLE}} -->", "")
        html = html.replace("<!-- {{/IF_LIFECYCLE}} -->", "")
        html = html.replace("{{IF_LIFECYCLE}}", "")
        html = html.replace("{{/IF_LIFECYCLE}}", "")
    else:
        # 移除生命周期块
        import re
        html = re.sub(
            r'<!--\s*\{\{IF_LIFECYCLE\}\}\s-->.*?<!--\s*\{\{/IF_LIFECYCLE\}\}\s-->',
            '', html, flags=re.DOTALL
        )
        html = re.sub(
            r'\{\{IF_LIFECYCLE\}\}.*?\{\{/IF_LIFECYCLE\}\}',
            '', html, flags=re.DOTALL
        )

    return html
