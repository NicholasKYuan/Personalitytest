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

SYSTEM_PROMPT = """你是专业的心理测评分析师，精通九型人格、MBTI、霍兰德职业兴趣理论和盖洛普优势识别器。
你的任务是根据用户的测评结果，生成一份深度、专业、有洞察力的个性化解读报告。

报告要求：
1. 使用 Markdown 格式，分章节输出
2. 全程使用简体中文撰写。**严格禁止输出任何英文单词、短语、句式或标题**（允许保留的极少量英文：MBTI/ISTP 等4字母类型代码、霍兰德 RIASEC 三字母代码——但出现时必须是代码本身，不要附带英文释义如 "ISTP (Introversion...)"）
3. **所有小标题（##、###、####）、列表项（-）、加粗强调（**...**）必须使用中文**，不得出现 "Growth direction"、"Fear:"、"Synergies and tensions"、"Relationship_building domain" 等英文标题
4. 描述九型人格时，用"动机与恐惧""核心特质""成长方向"等中文小节标题，不要用 "Motivations and fears"
5. 描述 MBTI 时，用"认知功能""思维模式""互动风格"等中文，不要用 "Thinking patterns"
6. 描述霍兰德时，用"代码解读""职业路径""发展建议"等中文，不要用 "EIS interpretation"
7. 描述盖洛普时，用中文主题名（如"审慎""专注""成就"），不要附英文原名
8. 描述综合解读时，用"协同点""张力点""融合洞察"等中文
9. 语言温暖、专业、有共感力，避免生硬的术语堆砌
10. 每个体系先解读核心特质，再给出发展建议
11. 四体系交叉解读要找出协同点和张力点，体现融合分析的价值
12. 结合用户的身份角色和测评目的，给出有针对性的建议
13. 总字数控制在 2000-3500 字
14. 如包含传统易学结合解读章节，用现代生涯规划语言表述，禁止出现八字、五行、紫微、占星等字眼，可使用"命理与心理的呼应"这一表述
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
        f"  {k}: {v}" for k, v in gallup["domains"].items()
    )
    gallup_themes_str = "、".join(gallup["top_themes"]) if gallup["top_themes"] else "暂无"

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
- 主导领域：{gallup['top_domain']}
- 领域得分：
{gallup_domains_str}
- 核心主题：{gallup_themes_str}

## 报告结构要求

请按以下章节输出。**注意：每个章节内部使用的中文小标题示例如下，请严格用中文，禁止任何英文小标题。**

### 1. 九型人格深度解读
解读 {enneagram['type_name']} 的核心特质、动机、恐惧、成长方向。
可使用以下中文小节标题：
- 核心画像（如"3号成就者"）
- 核心特质与内在动力
- 核心恐惧与盲区
- 成长方向

### 2. MBTI深度分析
分析 {mbti['type']} 的认知功能、思维模式、与他人的互动风格。
可使用以下中文小节标题：
- 类型定位
- 认知功能栈解读
- 互动风格分析
- 发展建议

### 3. 霍兰德职业方向
基于代码 {holland['code']}，推荐适合的职业方向和发展路径。
可使用以下中文小节标题：
- 代码解读（仅中文，不要 "R (Realistic...)" 这种格式）
- 适合的职业路径
- 相对不建议的方向

### 4. 盖洛普优势发挥
解读主导领域 {gallup['top_domain']} 和核心主题 {gallup_themes_str}，给出优势发挥和补盲建议。
**盖洛普的主题必须用其中文名**（如"审慎""专注""成就"），**禁止附带英文原名**（如不要写"Deliberative: 审慎"）。
可使用以下中文小节标题：
- 主导领域解读
- 核心主题解读（用纯中文名称）
- 补盲建议

### 5. 四体系综合交叉解读
找出四个体系之间的协同点和张力点，给出融合洞察。
可使用以下中文小节标题：
- 协同点
- 张力点
- 融合洞察
"""

    if birth_date:
        prompt += "\n### 6. 传统易学结合解读\n基于出生日期，用现代生涯规划语言提供命理与心理呼应的参考视角。禁止出现八字、五行、紫微、占星等字眼。\n"

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
        {"title": "九型人格深度解读", "content": f"## {en.get('main_type')}号 {en.get('type_name')}\n\n你的九型主型为 **{en.get('main_type')}号 {en.get('type_name')}**（MOCK）。"},
        {"title": "MBTI深度分析", "content": f"## {mb.get('type')}\n\n你的 MBTI 类型为 **{mb.get('type')}**（MOCK）。"},
        {"title": "霍兰德职业方向", "content": f"## {ho.get('code')}\n\n你的霍兰德代码为 **{ho.get('code')}**（MOCK）。"},
        {"title": "盖洛普优势发挥", "content": f"## {ga.get('top_domain')}\n\n主导领域 **{ga.get('top_domain')}**（MOCK）。"},
        {"title": "四体系综合交叉解读", "content": "## 综合视角\n\n四体系综合解读（MOCK）。"},
    ]
    return {"detailed_analysis": "", "sections": sections}


def _split_sections(markdown_text):
    """
    将 markdown 文本按 ## 或 ### 标题拆分为章节列表。
    """
    sections = []
    current_title = None
    current_lines = []

    for line in markdown_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("### ") or stripped.startswith("## "):
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

    return sections


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
    过滤掉 AI 输出中的英文过程文本/英文小标题/英文短语。
    移除纯英文行（允许 MBTI、霍兰德等缩写），保留中文内容。
    也过滤混合语言行中英文占比过高的行（如 AI 推理过程）。
    """
    lines = text.split('\n')
    filtered = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            filtered.append(line)
            continue

        # 跳过 Markdown 标题中的纯英文（### Growth direction）
        if re.match(r'^#{1,6}\s+[A-Za-z]', stripped):
            # 仅当整行没有中文字符时过滤
            if not re.search(r'[\u4e00-\u9fff]', stripped):
                continue

        # 跳过列表项中的英文短语（- Growth direction 或 * Fear: ...）
        if re.match(r'^[-*•]\s+[A-Za-z]', stripped):
            if not re.search(r'[\u4e00-\u9fff]', stripped):
                continue
            # 列表项有中文但前半部分是英文短语（如"- Growth direction 成长方向"），也过滤
            # 取冒号/破折号前的英文短语
            m = re.match(r'^[-*•]\s+([A-Za-z][A-Za-z\s\-,:&\(\)\.]+?)([\u4e00-\u9fff]|$)', stripped)
            if m and len(m.group(1).strip()) > 3:
                stripped = re.sub(r'^([-*•]\s+)[A-Za-z][A-Za-z\s\-,:&\(\)\.]+?(\s+)(?=[\u4e00-\u9fff])',
                                  r'\1', stripped)
                line = stripped

        # 跳过加粗英文标题（**Growth direction**）
        if re.match(r'^\*\*[A-Za-z][A-Za-z\s\-,:&\(\)\.]*\*\*$', stripped):
            if not re.search(r'[\u4e00-\u9fff]', stripped):
                continue

        # 跳过 "Foo: Bar" 这种英文标签行
        if re.match(r'^[A-Za-z][A-Za-z\s\-,:&\(\)\.]+:\s*[A-Za-z]', stripped):
            if not re.search(r'[\u4e00-\u9fff]', stripped):
                continue

        # 计算中文字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', stripped))
        # 计算英文单词数（排除常见缩写）
        clean = re.sub(r'\b(MBTI|RIASEC|ISTP|ISFP|INTJ|INFJ|ENTP|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ESTP|ESFP|ENTJ|ENFJ|RES|EIS|SIA|ASE|SEC|CSE|IA|SE|RE|RC|RI)\b', '', stripped)
        english_words = len(re.findall(r'[a-zA-Z]+', clean))

        # 如果一行几乎没有中文，且英文词较多，则判定为英文泄露
        if chinese_chars < 5 and english_words > 2:
            continue  # 跳过这行

        # 如果英文词比中文字符多，也是英文泄露（混合语言行）
        if english_words > chinese_chars and english_words > 3:
            continue

        # 跳过类似 "Here is..." "I'll..." "Let me..." 的过程文本
        if re.match(r'^(Here|I\'ll|Let me|Sure|Below|This is|The user|Now I|First|Second|Let\'s|I will|I need|I should|Birth date|Avoid|Note:|Important|The instruction|Since|Given)', stripped, re.IGNORECASE):
            continue

        # 跳过包含 AI 推理关键词的行
        if re.search(r'\b(avoid|forbidden|instruction|requirement|I can use|I\'ll talk|I should|mentioned|as allowed|says|allows|prompt|system prompt)\b', stripped, re.IGNORECASE):
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
