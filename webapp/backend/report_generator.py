#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
report_generator.py — 填充详细报告模板，生成可下载的 HTML 报告。
接收评分结果 + AI 分析章节，填充 report-detailed.html 模板。
"""
import json
import re
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


def _markdown_to_html(md):
    """简易 Markdown 转 HTML（支持标题、列表、加粗、表格）"""
    if not md:
        return ""
    # 转义
    md = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    lines = md.split("\n")
    html_parts = []
    in_ul = False
    in_ol = False
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        # 空行
        if not stripped:
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            i += 1
            continue

        # 表格检测：当前行以 | 开头，且下一行是分隔行（|---|---|）
        if stripped.startswith("|") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if re.match(r'^\|[\s\-:|]+\|$', next_line):
                # 收集表格行
                table_lines = [stripped]
                i += 2  # 跳过分隔行
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i].strip())
                    i += 1

                # 解析表格
                # 表头
                header_cells = [c.strip() for c in table_lines[0].strip("|").split("|")]
                html_parts.append('<table style="width:100%;border-collapse:collapse;margin:0.75rem 0;font-size:0.85rem;">')
                html_parts.append('<thead><tr>')
                for cell in header_cells:
                    html_parts.append(f'<th style="border:1px solid var(--border);padding:0.5rem;background:var(--bg);text-align:left;font-weight:700;">{cell}</th>')
                html_parts.append('</tr></thead>')
                # 数据行
                html_parts.append('<tbody>')
                for row_line in table_lines[1:]:
                    cells = [c.strip() for c in row_line.strip("|").split("|")]
                    html_parts.append('<tr>')
                    for cell in cells:
                        # 支持单元格内的加粗
                        cell_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cell)
                        html_parts.append(f'<td style="border:1px solid var(--border);padding:0.5rem;">{cell_html}</td>')
                    html_parts.append('</tr>')
                html_parts.append('</tbody></table>')
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
            i += 1
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
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', m.group(1))
            html_parts.append(f"<li>{text}</li>")
            i += 1
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
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', m.group(1))
            html_parts.append(f"<li>{text}</li>")
            i += 1
            continue

        # 段落
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False
        # 加粗：先开<strong>再闭</strong>，支持一行多组
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
        html_parts.append(f"<p>{text}</p>")
        i += 1

    if in_ul:
        html_parts.append("</ul>")
    if in_ol:
        html_parts.append("</ol>")

    return "\n".join(html_parts)


def _extract_section(sections, keywords):
    """从 AI sections 中按关键词提取内容，返回 HTML。"""
    for s in sections:
        title = s.get("title", "")
        for kw in keywords:
            if kw in title:
                return _markdown_to_html(s.get("content", ""))
    return ""


def _extract_subsection_from_content(content, keywords):
    """
    从一个 ## 章节的 markdown 内容中，按 ### 子标题关键词提取子章节内容。
    返回 HTML 格式的子章节内容（不含子标题本身），未找到则返回空字符串。
    """
    if not content:
        return ""
    lines = content.split("\n")
    current_sub_title = None
    current_sub_lines = []
    sub_sections = []  # [(sub_title, sub_content), ...]

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### ") or stripped.startswith("#### "):
            # 保存上一个子章节
            if current_sub_title is not None:
                sub_sections.append((current_sub_title, "\n".join(current_sub_lines).strip()))
            current_sub_title = stripped.lstrip("#").strip()
            current_sub_lines = []
        else:
            if current_sub_title is not None:
                current_sub_lines.append(line)
            # else: 属于章节开头但不在任何 ### 子标题下的内容，忽略

    # 保存最后一个子章节
    if current_sub_title is not None:
        sub_sections.append((current_sub_title, "\n".join(current_sub_lines).strip()))

    # 按关键词匹配
    for sub_title, sub_content in sub_sections:
        for kw in keywords:
            if kw in sub_title:
                return _markdown_to_html(sub_content)

    return ""


def _extract_section_content_only(sections, keywords):
    """从 AI sections 中按关键词提取原始 markdown 内容（不转 HTML）"""
    for s in sections:
        title = s.get("title", "")
        for kw in keywords:
            if kw in title:
                return s.get("content", "")
    return ""


# 四体系卡片配置：(体系关键词, 结果函数, css_class, 中文名, 图标)
_CROSS_SYSTEMS = [
    ("九型",   lambda r: f"{r.get('enneagram', {}).get('main_type', '')}号 {r.get('enneagram', {}).get('type_name', '')}".strip(), "en",  "九型人格", "🎭"),
    ("MBTI",  lambda r: r.get("mbti", {}).get("type", ""),                              "mbti", "MBTI", "🧩"),
    ("霍兰德", lambda r: r.get("holland", {}).get("code", ""),                           "ho",  "霍兰德", "🧭"),
    ("盖洛普", lambda r: GALLUP_DOMAIN_CN.get(r.get("gallup", {}).get("top_domain", ""), r.get("gallup", {}).get("top_domain", "未识别")), "ga", "盖洛普", "🏆"),
]


def _extract_synergy_tension(md_text, system_kw):
    """
    从交叉解读 markdown 中提取指定体系的协同信号和张力提示。
    格式：### 九型\n- 协同信号：...\n- 张力提示：...
    """
    if not md_text:
        return "", ""
    # 找到 ### 体系名 段落
    pattern = rf'###\s*{re.escape(system_kw)}[^\n]*\n(.*?)(?=###|\Z)'
    m = re.search(pattern, md_text, re.DOTALL)
    if not m:
        return "", ""
    block = m.group(1)
    synergy = ""
    tension = ""
    for line in block.split("\n"):
        line = line.strip()
        if "协同信号" in line:
            synergy = re.sub(r'^[-*]\s*协同信号[：:]\s*', '', line).strip()
        elif "张力提示" in line:
            tension = re.sub(r'^[-*]\s*张力提示[：:]\s*', '', line).strip()
    return synergy, tension


def _build_cross_cards(cross_md, results):
    """
    从交叉解读 markdown 生成 4 张体系卡片 HTML。
    每张卡包含：图标 + 体系名 + 主结果徽章 + 协同信号 + 张力提示。
    """
    if not cross_md:
        return ""

    cards = []
    for kw, result_fn, css_class, label, icon in _CROSS_SYSTEMS:
        main_value = result_fn(results)
        synergy, tension = _extract_synergy_tension(cross_md, kw)

        if not synergy and not tension:
            continue

        synergy_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', synergy) if synergy else ""
        tension_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', tension) if tension else ""

        card = f'''<div class="cross-sys-card">
    <div class="sys-head">
        <div class="sys-icon sys-icon--{css_class}">{icon}</div>
        <span class="sys-name">{label}</span>
        <span class="sys-badge sys-badge--{css_class}">{main_value}</span>
    </div>
    <div class="sys-synergy"><strong>✓ 协同信号</strong>{synergy_html}</div>
    <div class="sys-tension"><strong>⚠ 张力提示</strong>{tension_html}</div>
</div>'''
        cards.append(card)

    return "\n".join(cards)


# 霍兰德代码对应的默认职业方向（当 AI 输出无法提取职业列表时使用）
HOLLAND_DEFAULT_CAREERS = {
    "R": ["工程师", "技术员", "建筑师", "农艺师", "运动员"],
    "I": ["科研人员", "数据分析师", "医生", "大学教授", "产品研究员"],
    "A": ["设计师", "作家", "音乐人", "导演", "创意策划"],
    "S": ["教师", "心理咨询师", "社工", "人力资源", "培训师"],
    "E": ["创业者", "市场营销", "项目经理", "律师", "销售总监"],
    "C": ["会计师", "审计师", "行政主管", "数据库管理员", "财务分析师"],
}


def _extract_career_list(ai_sections, holland_code):
    """
    从 AI 霍兰德章节中提取职业推荐列表，生成 HTML <li> 项。
    如果无法提取，回退到基于霍兰德代码的默认职业列表。
    """
    holland_md = _extract_section_content_only(ai_sections, ["霍兰德", "职业", "方向"])
    careers = []

    if holland_md:
        lines = holland_md.split("\n")
        for line in lines:
            stripped = line.strip()
            # 匹配列表项: "- 职业名称" 或 "1. 职业名称" 或 "**职业名称**"
            # 也匹配行内包含职业名称的加粗文本
            m = re.match(r'^[-*]\s+(.+)', stripped)
            if not m:
                m = re.match(r'^\d+[\.\)]\s+(.+)', stripped)
            if m:
                text = m.group(1).strip()
                # 去掉 markdown 加粗标记，提取纯文本
                text_clean = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
                # 只取较短的行作为职业名（避免把整段分析当职业名）
                if len(text_clean) <= 30 and text_clean:
                    careers.append(text_clean)
            elif not careers:
                # 尝试提取加粗的职业名
                bold_matches = re.findall(r'\*\*(.+?)\*\*', stripped)
                for bm in bold_matches:
                    bm_clean = bm.strip()
                    # 过滤掉太长或明显不是职业名的
                    if 2 <= len(bm_clean) <= 15 and not any(kw in bm_clean for kw in ["代码", "霍兰德", "类型", "得分"]):
                        # 过滤掉类似霍兰德代码的全大写短字符串（如 REC、EAS）
                        if not (len(bm_clean) <= 3 and bm_clean.isupper()):
                            careers.append(bm_clean)

    # 去重，最多取 8 个
    seen = set()
    unique_careers = []
    for c in careers:
        if c not in seen:
            seen.add(c)
            unique_careers.append(c)
        if len(unique_careers) >= 8:
            break

    # 回退到默认职业列表
    if not unique_careers and holland_code:
        for code_char in holland_code[:3]:
            defaults = HOLLAND_DEFAULT_CAREERS.get(code_char, [])
            for d in defaults[:3]:
                if d not in seen:
                    seen.add(d)
                    unique_careers.append(d)
                if len(unique_careers) >= 6:
                    break
            if len(unique_careers) >= 6:
                break

    if not unique_careers:
        unique_careers = ["请参考霍兰德代码对应的职业方向"]

    # 生成 HTML
    icons = ["💼", "🎯", "🚀", "📋", "🔬", "🎨", "📊", "🤝"]
    html_parts = []
    for i, career in enumerate(unique_careers):
        icon = icons[i % len(icons)]
        html_parts.append(f'<li><span class="career-icon">{icon}</span>{career}</li>')

    return "".join(html_parts)


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
    career_list_html = _extract_career_list(ai_sections, holland_code)

    # AI 章节内容
    enneagram_analysis = _extract_section(ai_sections, ["九型", "enneagram"])
    mbti_analysis = _extract_section(ai_sections, ["MBTI", "mbti"])
    holland_analysis = _extract_section(ai_sections, ["霍兰德", "holland", "职业"])
    gallup_analysis = _extract_section(ai_sections, ["盖洛普", "gallup", "优势"])

    # 综合交叉解读：提取章节原始 markdown，用于后续子章节提取
    cross_section_md = _extract_section_content_only(ai_sections, ["交叉", "综合", "cross"])
    cross_analysis = _markdown_to_html(cross_section_md) if cross_section_md else ""

    # 四体系交叉解读卡片 + 融合洞察
    cross_cards_html = ""
    insight_html = ""
    if cross_section_md:
        cross_cards_html = _build_cross_cards(cross_section_md, results)
        insight_md = _extract_subsection_from_content(cross_section_md, ["融合洞察", "insight", "洞察"])
        if insight_md:
            insight_html = insight_md

    # 易学/生涯发展时机建议章节
    lifecycle_content = ""
    lifecycle_focus = ""
    lifecycle_pitfall = ""
    lifecycle_cross = ""
    if birth_date:
        lifecycle_md = _extract_section_content_only(ai_sections, ["易学", "传统", "命理", "生涯", "lifecycle"])
        if lifecycle_md:
            # 尝试从 ### 子标题中提取4个子板块
            lifecycle_content = _extract_subsection_from_content(lifecycle_md, ["当前", "定位"])
            lifecycle_focus = _extract_subsection_from_content(lifecycle_md, ["专注", "方向"])
            lifecycle_pitfall = _extract_subsection_from_content(lifecycle_md, ["避坑", "提醒", "注意"])
            lifecycle_cross = _extract_subsection_from_content(lifecycle_md, ["交叉", "印证", "验证"])
            # 如果没有子标题结构，把全部内容放在 LIFECYCLE_CURRENT
            if not lifecycle_content and not lifecycle_focus and not lifecycle_pitfall and not lifecycle_cross:
                lifecycle_content = _markdown_to_html(lifecycle_md)

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

        "{{CAREER_LIST}}": career_list_html,
        "{{GALLUP_THEME_TAGS}}": theme_tags,

        "{{ENNEAGRAM_ANALYSIS}}": enneagram_analysis,
        "{{MBTI_ANALYSIS}}": mbti_analysis,
        "{{HOLLAND_ANALYSIS}}": holland_analysis,
        "{{GALLUP_ANALYSIS}}": gallup_analysis,
        "{{CROSS_ANALYSIS}}": cross_analysis,
        "{{CROSS_CARDS}}": cross_cards_html,
        "{{INSIGHT_POINTS}}": insight_html,
        # 旧版兼容（保留为空，不再被模板使用）
        "{{CROSS_TABLE}}": "",
        "{{SYNERGY_POINTS}}": "",
        "{{TENSION_POINTS}}": "",

        "{{LIFECYCLE_CURRENT}}": lifecycle_content if lifecycle_content else "",
        "{{LIFECYCLE_FOCUS}}": lifecycle_focus if lifecycle_focus else "",
        "{{LIFECYCLE_PITFALL}}": lifecycle_pitfall if lifecycle_pitfall else "",
        "{{LIFECYCLE_CROSS}}": lifecycle_cross if lifecycle_cross else "",
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
        html = re.sub(
            r'<!--\s*\{\{IF_LIFECYCLE\}\}\s-->.*?<!--\s*\{\{/IF_LIFECYCLE\}\}\s-->',
            '', html, flags=re.DOTALL
        )
        html = re.sub(
            r'\{\{IF_LIFECYCLE\}\}.*?\{\{/IF_LIFECYCLE\}\}',
            '', html, flags=re.DOTALL
        )

    return html
