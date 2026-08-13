#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_analyzer.py — Minimax M3 深度分析集成
调用 Minimax M3 API 生成四体系深度解读报告。
"""
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None

def _get_client():
    """延迟初始化 OpenAI 客户端，避免模块导入时因缺少 API Key 崩溃。"""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("MINIMAX_API_KEY", "mock-key"),
            base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1"),
        )
    return _client

MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M3")

# 盖洛普 34 主题中文名映射（传入 AI prompt 前转中文）
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

# 盖洛普四领域中文名映射
GALLUP_DOMAIN_NAMES = {
    "executing": "执行力",
    "influencing": "影响力",
    "relationship_building": "关系建立",
    "strategic_thinking": "战略思维",
}

SYSTEM_PROMPT = """你是专业的心理测评分析师，精通九型人格、MBTI、霍兰德职业兴趣理论和盖洛普优势识别器。
你的任务是根据用户的测评结果，生成一份深度、专业、有洞察力的个性化解读报告。

报告要求（务必严格遵守）：

1. 使用 Markdown 格式，分章节输出。

2. **写作方式：禁止先列 outline 再展开**。不要在每个章节内先写"我会讲：动机、恐惧、成长方向"这种 outline 列表，请直接以完整段落（每段 80-150 字）开始阐述，让读者立刻进入深度解读。

3. 主要使用简体中文撰写，中英文混排可以接受（如保留 MBTI、ISTP 等类型代码），但章节小标题请优先使用中文。

4. 描述九型人格时，用"核心特质""内在动力""潜在盲区""成长方向"等中文小节标题。

5. 描述 MBTI 时，用"类型定位""认知功能栈""互动风格""发展建议"等中文。

6. 描述霍兰德时，用"代码解读""适合的职业方向""发展路径"等中文。

7. 描述盖洛普时，用中文主题名（如"审慎""专注""成就"）。

8. 描述综合解读时，用"协同点""张力点""融合洞察"等中文。

9. 语言温暖、专业、有共感力，避免生硬的术语堆砌。

10. 每个体系的核心解读要直接进入深度分析（不是"该类型的特点是..."这种教科书腔），要结合用户的角色、目的、当下状态给出个性化洞察。

11. 四体系交叉解读要找出协同点和张力点，体现融合分析的价值。

12. 总字数控制在 2000-3500 字。

13. 如包括传统易学结合解读章节，用现代生涯规划语言表述，禁止出现八字、五行、紫微、占星等字眼，可使用"命理与心理的呼应"这一表述。
"""


def _build_user_prompt(results, profile):
    """构建发送给 LLM 的 user prompt。"""
    enneagram = results["enneagram"]
    mbti = results["mbti"]
    holland = results["holland"]
    gallup = results["gallup"]

    # 九型各类型得分
    enneagram_scores_str = "\n".join(
        f"  {k}: {v}" for k, v in enneagram["scores"].items()
    )

    # MBTI 各维度得分
    mbti_dims_str = "\n".join(
        f"  {k}: {v}" for k, v in mbti["dimensions"].items()
    )

    # 霍兰德各类型得分
    holland_scores_str = "\n".join(
        f"  {k}: {v}" for k, v in holland["scores"].items()
    )

    # 盖洛普领域得分
    gallup_domains_str = "\n".join(
        f"  {GALLUP_DOMAIN_NAMES.get(k, k)}: {v}" for k, v in gallup["domains"].items()
    )
    # 盖洛普主题名转中文后传入 prompt
    gallup_themes_cn = [GALLUP_THEME_NAMES.get(t, t) for t in gallup["top_themes"]]
    gallup_themes_str = "、".join(gallup_themes_cn) if gallup_themes_cn else "暂无"

    # 用户信息
    name = profile.get("name", "用户")
    age = profile.get("age", "未知")
    gender = profile.get("gender", "未知")
    role = profile.get("role", "未知")
    purpose = profile.get("purpose", "未知")
    current_state = profile.get("current_state", "未知")
    birth_date = profile.get("birth_date", "")

    gender_map = {"male": "男", "female": "女", "other": "其他", "prefer-not-to-say": "不愿透露"}
    gender_str = gender_map.get(gender, str(gender))

    prompt = f"""请为以下用户生成深度测评解读报告。

## 用户信息
- 姓名/称呼：{name}
- 年龄：{age}
- 性别：{gender_str}
- 身份角色：{role}
- 测评目的：{purpose}
- 当下状态：{current_state}
"""

    if birth_date:
        prompt += f"- 出生日期：{birth_date}（用于传统易学结合解读）\n"

    prompt += f"""
## 测评结果

### 九型人格
- 主型：{enneagram['main_type']}号 - {enneagram['type_name']}
- 各类型得分：
{enneagram_scores_str}

### MBTI
- 类型：{mbti['type']}
- 各维度得分：
{mbti_dims_str}

### 霍兰德职业兴趣
- 代码：{holland['code']}
- 各类型得分：
{holland_scores_str}

### 盖洛普优势
- 主导领域：{GALLUP_DOMAIN_NAMES.get(gallup['top_domain'], gallup['top_domain'])}
- 领域得分：
{gallup_domains_str}
- 核心主题：{gallup_themes_str}

## 报告结构要求

请按以下章节输出。章节内的小标题优先用中文（中英文混排可接受）。

### 1. 九型人格深度解读
解读 {enneagram['type_name']} 的核心特质、动机、恐惧、成长方向。

### 2. MBTI深度分析
分析 {mbti['type']} 的认知功能、思维模式、与他人的互动风格。

### 3. 霍兰德职业方向
基于代码 {holland['code']}，推荐适合的职业方向和发展路径。

### 4. 盖洛普优势发挥
解读主导领域 {GALLUP_DOMAIN_NAMES.get(gallup['top_domain'], gallup['top_domain'])} 和核心主题 {gallup_themes_str}，给出优势发挥和补盲建议。

### 5. 四体系综合交叉解读
找出四个体系之间的协同点和张力点，给出融合洞察。请务必使用以下子标题结构：

### 协同点
（列出2-3个四体系之间的协同亮点）

### 张力点
（列出1-2个四体系之间的张力或潜在冲突）

### 融合洞察
（综合四体系的整体洞察）
"""

    if birth_date:
        prompt += "\n### 6. 传统易学结合解读\n基于出生日期，用现代生涯规划语言提供命理与心理呼应的参考视角。禁止出现八字、五行、紫微、占星等字眼。请务必使用以下4个子标题，每个80-150字：\n\n### 当前发展阶段定位\n（分析用户当前所处的人生发展阶段）\n\n### 近三年专注方向\n（建议未来1-3年的核心发展方向）\n\n### 阶段性格避坑提醒\n（提示当前阶段需要避免的陷阱）\n\n### 与四体系交叉验证\n（将易学视角与MBTI/九型/霍兰德/盖洛普四体系结果相互印证，必须有具体引用）\n"

    prompt += "\n请确保报告专业、深入、有个性化洞察。"
    return prompt


def generate_detailed_analysis(results, profile):
    """
    调用 Minimax M3 生成深度解读。

    Args:
        results: score_answers() 的返回值
        profile: 用户信息 dict

    Returns:
        dict: {
            "detailed_analysis": "完整 markdown 文本",
            "sections": [{"title": "...", "content": "..."}, ...]
        }
    """
    # AI_MOCK=1：返回固定章节，便于无 API Key / 联调时走通完整流程
    if os.getenv("AI_MOCK", "0") == "1":
        return _mock_sections(results, profile)

    user_prompt = _build_user_prompt(results, profile)

    try:
        response = _get_client().chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=8000,
        )
        content = response.choices[0].message.content
    except Exception as e:
        # 降级：返回错误信息
        content = f"## 深度分析生成失败\n\n抱歉，AI 深度分析服务暂时不可用。\n\n错误信息：{str(e)}"

    # 第一步：过滤禁用词（在任何其他处理之前，确保全文替换）
    content = _filter_forbidden_words(content)

    # 第二步：过滤英文泄露
    content = _filter_english(content)

    # 第三步：移除首个 markdown 标题前的 AI 推理过程
    content = _strip_preface(content)

    # 第四步：再次过滤禁用词（防止推理文本被部分移除后新暴露的词）
    content = _filter_forbidden_words(content)

    # 将 markdown 按章节拆分
    sections = _split_sections(content)

    # 第五步：检查章节内容质量。如果某个章节过滤后内容太短（< 100 字），
    # 标记 incomplete，前端会显示"重新生成"按钮。保留原始内容不替换。
    for sec in sections:
        if len(sec["content"]) < 100:
            sec["incomplete"] = True

    return {
        "detailed_analysis": content,
        "sections": sections,
    }


def _mock_sections(results, profile):
    """AI_MOCK 模式下的固定章节（结构对齐真实输出，供联调/测试）。"""
    en = results.get("enneagram", {})
    mb = results.get("mbti", {})
    ho = results.get("holland", {})
    ga = results.get("gallup", {})
    sections = [
        {"title": "九型人格深度解读", "content": f"## {en.get('main_type')}号 {en.get('type_name')}\n\n你的九型主型为 **{en.get('main_type')}号 {en.get('type_name')}**（MOCK）。核心特质包括追求卓越、关注效率与形象管理。内在动力源于对成功和认可的渴望，恐惧被否定或被视为失败者。成长方向是学会真实地连接他人，而非仅通过成就获得认可。"},
        {"title": "MBTI深度分析", "content": f"## {mb.get('type')}\n\n你的 MBTI 类型为 **{mb.get('type')}**（MOCK）。认知功能栈以思维和判断为主导，擅长系统性分析和目标导向的执行。互动风格直接高效，偏好结构化的沟通方式。发展建议是培养对他人情感的感知力，在决策中适当融入人文关怀。"},
        {"title": "霍兰德职业方向", "content": f"## {ho.get('code')}\n\n你的霍兰德代码为 **{ho.get('code')}**（MOCK）。基于该代码组合，推荐以下职业方向：\n- 产品经理\n- 项目管理\n- 市场战略\n- 创业运营\n- 数据分析\n- 管理咨询\n这些方向既匹配你的实际型和企业型倾向，也能发挥你在执行和战略方面的优势。"},
        {"title": "盖洛普优势发挥", "content": f"## {ga.get('top_domain')}\n\n主导领域 **{ga.get('top_domain')}**（MOCK）。核心主题包括成就、专注和统筹。优势发挥建议：在目标明确的环境中你能够高效产出，适合担任推动落地的角色。补盲建议：注意在追求效率时不要忽视团队的情感需求，适当放慢节奏倾听不同声音。"},
        {"title": "四体系综合交叉解读", "content": "## 综合视角\n\n### 协同点\n\n四体系协同解读（MOCK）：九型成就者与MBTI判断型高度一致，驱动执行力。盖洛普执行力领域进一步强化了目标达成能力。霍兰德企业型倾向与九型成就动机形成正向循环。\n\n### 张力点\n\n九型的形象关注与MBTI直觉型的抽象偏好存在张力。霍兰德实际型偏好与盖洛普关系建立领域的薄弱可能影响团队协作。\n\n### 融合洞察\n\n综合来看，该用户适合目标导向的创造型工作。建议在保持高效执行的同时，有意识地培养人际感知力，以实现更全面的领导力发展。"},
    ]

    # 当存在 birth_date 时，添加第 6 章
    if profile.get("birth_date"):
        sections.append({
            "title": "传统易学结合解读",
            "content": '## 命理与心理的呼应\n\n### 当前发展阶段定位\n\n（MOCK）结合您的出生年月日，当前正处于事业上升期，能量场偏向行动与突破。这是建立核心竞争力和拓展影响力的关键阶段。\n\n### 近三年专注方向\n\n（MOCK）建议未来 1-3 年聚焦于专业深度的建立和资源网络的拓展。适合主导创新型项目，将个人能力转化为可复制的系统。\n\n### 阶段性格避坑提醒\n\n（MOCK）当前阶段需注意避免过度自信导致的决策仓促。在高速发展中容易忽略细节和人际维护，建议定期复盘并保持与导师的对话。\n\n### 与四体系交叉验证\n\n（MOCK）九型 8 号的挑战者特质与当前命理阶段的突破能量高度吻合。MBTI 判断型偏好与「事业上升期」的节奏匹配。霍兰德企业型倾向在当前阶段有天然优势。盖洛普执行力领域的强势为这一阶段提供了坚实的行动力基础。'
        })

    return {"detailed_analysis": "", "sections": sections}


def _split_sections(markdown_text):
    """
    将 markdown 文本按 ## 标题拆分为章节列表。
    只按二级标题（##）拆分，### 子标题保留在父章节内。
    """
    sections = []
    current_title = None
    current_lines = []

    for line in markdown_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            # 保存上一个章节
            if current_title is not None:
                sections.append({
                    "title": current_title,
                    "content": "\n".join(current_lines).strip(),
                })
            # 去掉 markdown 标题符号
            current_title = stripped.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    # 保存最后一个章节
    if current_title is not None:
        sections.append({
            "title": current_title,
            "content": "\n".join(current_lines).strip(),
        })

    # 如果没有找到任何标题，返回整体
    if not sections:
        sections.append({
            "title": "深度解读报告",
            "content": markdown_text.strip(),
        })

    # 去重：AI 有时会输出两遍报告（简版+详版），同名章节保留内容更长的
    seen = {}
    for sec in sections:
        key = sec["title"].strip()
        if key not in seen or len(sec["content"]) > len(seen[key]["content"]):
            seen[key] = sec
    sections = list(seen.values())

    # 合并短章节：内容 < 150 字的章节合并到前一个章节
    # 这解决 AI 输出过多 ## 子标题（核心特质、内在动力等各自独立）的问题
    merged = []
    for sec in sections:
        if merged and len(sec["content"]) < 150:
            # 短章节：追加到前一个章节
            prev = merged[-1]
            prev["content"] += "\n\n" + "### " + sec["title"] + "\n\n" + sec["content"]
        else:
            merged.append(sec)

    return merged


def _strip_preface(text):
    """
    移除首个 markdown 标题前的 AI 推理过程文本。
    Minimax M3 有时会在正式内容前输出思考过程。
    无条件移除第一个 ## 或 ### 标题之前的所有内容。
    """
    lines = text.split('\n')
    first_heading_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('## ') or stripped.startswith('### '):
            first_heading_idx = i
            break
    if first_heading_idx is not None and first_heading_idx > 0:
        return '\n'.join(lines[first_heading_idx:])
    return text


def _filter_english(text):
    """
    过滤掉 AI 输出中的过程文本（如 "Here is..."、"I'll..." 等推理过程）。
    中英文混排可以接受，不过滤英文小标题或短语。
    但纯英文段落（无中文字符的连续多行英文）会被移除。

    优化点：
    - 中文豁免阈值从 10 提高到 15 个汉字，减少误删
    - 关键词列表收窄为 AI 推理最强信号词
    - "Note:" / "Important" 开头的行仅在无中文字符时才跳过
    """
    lines = text.split('\n')
    filtered = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            filtered.append(line)
            continue

        # 统计中文字符数
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', stripped)
        has_chinese = len(chinese_chars) > 0
        chinese_count = len(chinese_chars)

        # 跳过 AI 推理过程文本（"Here is...", "I'll...", "Let me..." 等）
        # 仅在行首匹配，且后面紧跟空格或标点
        if re.match(r'^(Here |I\'ll |Let me |Sure,|Below is|This is |The user |Now I |First,|Second,|Let\'s |I will |I need |I should |Given |Since )', stripped, re.IGNORECASE):
            # 但如果该行有 >= 15 个中文字符，可能是正文碰巧以这些词开头，保留
            if chinese_count < 15:
                continue

        # 跳过包含 AI 推理关键词的行（仅最强信号词）
        # 收窄列表：只保留 AI 推理过程中几乎不会出现在正文中的词
        if re.search(r'\b(system prompt|as allowed|I\'ll talk|I should (not|avoid|mention))\b', stripped, re.IGNORECASE):
            if chinese_count < 15:
                continue

        # "Note:" / "Important" 开头的行：仅在无中文时才跳过
        if re.match(r'^(Note:|Important:|The instruction|Birth date|Avoid )', stripped, re.IGNORECASE):
            if not has_chinese:
                continue

        # 过滤纯英文段落：行中没有任何中文字符 + 英文单词 > 8 个
        if not has_chinese and not stripped.startswith('#'):
            english_word_count = len(re.findall(r'[a-zA-Z]+', stripped))
            # 排除 MBTI/霍兰德等类型代码行
            is_code_line = bool(re.match(r'^(MBTI|RIASEC|ISTP|ISFP|INTJ|INFJ|ENTP|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ESTP|ESFP|ENTJ|ENFJ|RES|EIS|SIA|ASE|SEC|CSE|IA|SE|RE|RC|RI)\b', stripped))
            if english_word_count > 8 and not is_code_line:
                continue

        filtered.append(line)

    return '\n'.join(filtered)


def _filter_forbidden_words(text):
    """
    替换 AI 输出中的禁用词。
    将八字/五行/紫微/占星等替换为安全表述。
    注意："命理"不在替换列表中，因为"命理与心理的呼应"是允许使用的表述。
    """
    replacements = {
        '八字': '生命格局',
        '五行': '生命元素',
        '紫微': '星象传统',
        '占星': '天文传统',
        '盲派': '传统学派',
        '四柱': '生命坐标',
        '天干地支': '传统时序',
        '十神': '生命角色',
        '大运': '人生阶段',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text
