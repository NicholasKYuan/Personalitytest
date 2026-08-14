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

1. 使用 Markdown 格式，分章节输出。每个章节标题必须用 `## ` 开头。

2. **禁止只输出大纲**。每个章节必须有完整的正文段落（每段 80-150 字），不能只列子标题。例如，不能只写"### 核心特质\n### 内在动力"然后跳到下一个章节，必须在每个子标题下写出完整的分析段落。

3. **禁止先列 outline 再展开**。不要在每个章节内先写"我会讲：动机、恐惧、成长方向"这种 outline 列表，请直接以完整段落开始阐述。

4. 主要使用简体中文撰写，中英文混排可以接受（如保留 MBTI、ISTP 等类型代码），但章节小标题请优先使用中文。

5. 描述九型人格时，用"核心特质""内在动力""潜在盲区""成长方向"等中文小节标题。

6. 描述 MBTI 时，用"类型定位""认知功能栈""互动风格""发展建议"等中文。

7. 描述霍兰德时，用"代码解读""适合的职业方向""发展路径"等中文。

8. 描述盖洛普时，用中文主题名（如"审慎""专注""成就"）。

9. 描述综合解读时，用"协同点""张力点""融合洞察"等中文。

10. 语言温暖、专业、有共感力，避免生硬的术语堆砌。

11. 每个体系的核心解读要直接进入深度分析（不是"该类型的特点是..."这种教科书腔），要结合用户的角色、目的、当下状态给出个性化洞察。

12. 四体系交叉解读要找出协同点和张力点，体现融合分析的价值。

13. 总字数控制在 2000-3500 字。每个章节至少 300 字。

14. 传统易学结合解读章节必须输出（无论用户是否填了出生日期，都需基于年龄/角色推断发展阶段）。用现代生涯规划语言表述，禁止出现八字、五行、紫微、占星等字眼，可使用"命理与心理的呼应"这一表述。

15. **禁止输出任何自检清单、验证清单或思考过程**。不要在报告末尾输出类似"1. ✅ Markdown format""2. ✅ Simplified Chinese"等自检条目。报告写完即结束，不要附加任何"I think this is good""Let me check"等AI自我评价文本。

16. **禁止输出报告外的任何内容**：不要在报告前后添加"报告生成完毕""以下是报告"等元文本，直接输出章节内容。

17. **禁止输出思考过程**：不要在报告中分析你的写作思路、不要解释你为什么要这样写、不要输出英文分析笔记。直接输出中文报告正文。
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

## 报告质量约束（务必遵守，测试员2026-08-13反馈）

### 一、避免过度推断（适用于所有章节）
- 用"倾向""可能""通常"，不用"绝对""一定""必然"
- 最高分只能说"最突出的核心倾向"或"核心倾向最明显"，不写"绝对主导""遥遥领先""天生擅长"
- 用户的职业/教育/身份信息只作为背景参考，不基于此推论人格特质或价值观
- 关系场景的解读用"可能先退回思考""可能延后表达需求""较少主动发问"等弱化表述，不用"回避""导致不被理解""回避真正亲近""在场却缺席"等强推断
- 成长建议不预设用户有感情问题，不写"回应伴侣情绪"等关系专属动作；改成通用可操作动作（例：少一点过度准备，达到足够信息后先行动；沟通时先回应，再分析）
- 命中率达到"决策建议"层级即可，不追求"预言结论"

### 二、各章节技术要点

#### MBTI
- 认知功能顺序必须按标准理论：ENFP: Ne-Ti-Fe-Si（注意第3位是Fe不是Si）；INTJ: Ni-Te-Fi-Se；等等。避免错写成"Ne→Ti→Si→Fe"
- E54/146（外向直觉得分高 + 内向实感得分高）不要过度解读为"社交后一定需要长时间独处恢复"——只需要说明"社交后倾向短暂独处、较少主动分享话题、对象和场景偏好更窄"等弱化事实
- Fe不在第1-2位不等于"看不懂别人情绪"，可描述为"识别他人情绪没问题，但处理问题时通常先走分析系统，再顾及情绪"
- 必要时补上"自身情绪识别滞后"——情绪反向进入意识，有时要到惊慌/疲惫/身体不适才察觉
- P（实感-直觉维度后者）不等于"执行力差"，实为"保留选择+边走边调整+倾向于早做方案"——结合Ti和现实任务，遇到重要项目完全可以自主建立规则、节点、复盘
- 成长建议要给出可操作动作，不要只写"训练Fe/Si"等抽象表述

#### 霍兰德
- 同分类型只能说"X型与Y型并列突出"或"X与Y同分"，不下"AIE"等带顺序的代码结论
- 强调"职业兴趣偏好"而非"能力鉴定"——避免"非常典型的创意型/知识工作者"等定论式表达
- 描述代码时用"对XX类活动兴趣最高"，而非"你是XX型工作者"
- 职业推荐分两层："职业特征描述"+"匹配职业例子"——例：先说"对结构性问题的拆解和策略设计有持续兴趣，且不排斥推动落地"，再举2-4个职业例子
- 不要基于用户年龄/职业身份做具体的生涯推论（如"27岁自由职业者"）
- E（企业型）得分只代表"对推动事情、影响他人或商业化并不排斥"，不等于"已经具备对外争取资源能力"
- 发展空间用"找交叉点作为核心优势，再用E帮助成果落地"的思路，不要锁定单一技能

#### 盖洛普
- 主题分数（如50/32/26/23）只说明"主题主要集中在XX领域"，不写"遥遥领先""天生擅长""核心突出到XX分以上"
- 战略思维领域得分高不等于"亲密关系能力"——避免从工作优势强行跨越到亲密关系
- 主题拆解要分"工作/决策中的表现"与"关系中可选择的应用"，避免硬拼成"性格画像"
- 领域分数低只代表"非首选执行路径"，不等同于"快速行动差""影响别人能力弱"等能力否定
- 补盲建议要具体到动作（"对每个战略决策设截止点+责任人+下一步动作"），不写"每周主动安排"等空泛建议
- 5个主题组合可以保留，但要说明"这5个主题的组合在[用做决策/用做规划/用做回应]时的表现更明显"

#### 传统易学章节
- 本章只使用：①四体系测评稳定信息 ②年龄 ③隐性的传统节律推断，不引用用户具体职业/教育/身份/婚姻状态
- "扎根期""上升期""转折期"等表述必须明确至少1个具体方向：职业方向收束 / 能力标签成形 / 关系边界明确 / 生活结构稳定
- 未来1~3年写成"策略窗口"（"未来1~3年更适合采用的策略是……"），不写成预言结论
- 四体系交叉验证只提炼2-3个跨体系同时出现的主题（例如"高探索倾向+高自主性+高战略思维"+主要风险），要真正写出共同结论，避免重复各模块解读
- 最后的避坑提醒用"矛盾识别"思路——找到2个内在张力的维度（例"保持开放"与"形成长期积累"之间的冲突），给出"如何在该张力下做出选择"的方向，不写说教句（如"你已经过了XX年龄"）
- 不出现具体职业身份相关的内容（如"自由职业""自由接单""远程办公"等）

## 报告结构要求

请按以下章节输出，每个章节标题必须用 `## ` 开头（二级标题），章节内的小标题用 `### ` 开头（三级标题）。

## 1. 九型人格深度解读
解读 {enneagram['type_name']} 的核心特质、动机、恐惧、成长方向。

## 2. MBTI深度分析
分析 {mbti['type']} 的认知功能、思维模式、与他人的互动风格。

## 3. 霍兰德职业方向
基于代码 {holland['code']}，推荐适合的职业方向和发展路径。

## 4. 盖洛普优势发挥
解读主导领域 {GALLUP_DOMAIN_NAMES.get(gallup['top_domain'], gallup['top_domain'])} 和核心主题 {gallup_themes_str}，给出优势发挥和补盲建议。
"""

    # === 第 5 节：四体系综合交叉解读（无论有无出生日期都输出） ===
    prompt += """
## 5. 四体系综合交叉解读
请按以下结构输出，每个体系一个 ### 子标题，内含协同信号和张力提示两个要点，最后写融合洞察段落。

### 九型
- 协同信号：1-2句概括九型结果与其他体系相互呼应的亮点
- 张力提示：1句指出九型维度的潜在盲点/代价

### MBTI
- 协同信号：1-2句概括MBTI结果与其他体系相互呼应的亮点
- 张力提示：1句指出MBTI维度的潜在盲点/代价

### 霍兰德
- 协同信号：1-2句概括霍兰德结果与其他体系相互呼应的亮点
- 张力提示：1句指出霍兰德维度的潜在盲点/代价

### 盖洛普
- 协同信号：1-2句概括盖洛普结果与其他体系相互呼应的亮点
- 张力提示：1句指出盖洛普维度的潜在盲点/代价

### 融合洞察
（输出 2-3 段，150-250 字，先给出一个主题句概括"你是什么样的 X"，再展开为什么四体系都指向同一方向，最后给一句具体的实践建议）
"""

    if birth_date:
        # 有出生日期：用出生日期做"命理与心理呼应"的参考维度
        prompt += f"\n## 6. 传统易学结合解读\n基于出生日期 {birth_date}（用户年龄约 {age} 岁），用现代生涯规划语言提供命理与心理呼应的参考视角。禁止出现八字、五行、紫微、占星等字眼。请务必使用以下4个子标题，每个80-150字：\n\n### 当前发展阶段定位\n（基于出生日期推断用户当前所处的人生发展阶段及其典型特征）\n\n### 近三年专注方向\n（基于发展阶段，建议未来1-3年的核心发展方向）\n\n### 阶段性格避坑提醒\n（提示当前阶段需要避免的常见陷阱）\n\n### 与四体系交叉验证\n（将易学视角与MBTI/九型/霍兰德/盖洛普四体系结果相互印证，必须有具体引用）\n"
    else:
        # 无出生日期：用年龄+身份角色推断所处人生阶段，给出"年龄段+职业期"的参考视角
        prompt += f"\n## 6. 传统易学结合解读\n用户未填写出生日期，请基于年龄（{age}岁）+ 身份角色（{role}）推断当前所处的人生发展阶段，用现代生涯规划语言提供命理与心理呼应的参考视角。禁止出现八字、五行、紫微、占星等字眼。请务必使用以下4个子标题，每个80-150字：\n\n### 当前发展阶段定位\n（基于年龄推断用户当前所处的人生发展阶段及其典型特征——例如学生期/初入职场/职业成长期/中年转型期/资深沉淀期）\n\n### 近三年专注方向\n（基于年龄段+身份角色，建议未来1-3年的核心发展方向）\n\n### 阶段性格避坑提醒\n（提示当前阶段需要避免的常见陷阱）\n\n### 与四体系交叉验证\n（将易学视角与MBTI/九型/霍兰德/盖洛普四体系结果相互印证，必须有具体引用）\n"

    prompt += "\n请确保报告专业、深入、有个性化洞察。"
    return prompt


def _is_low_quality(sections, content):
    """检查 AI 输出质量是否过低，需要重试。"""
    # 章节数量不足（应至少有 4 个章节）
    if len(sections) < 4:
        return True
    # 总字数过少（应至少 1500 字）
    total_chars = sum(len(s["content"]) for s in sections)
    if total_chars < 1500:
        return True
    # 中文字符占比过低（英文大纲/笔记）
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    if total_chars > 0 and chinese_chars / max(total_chars, 1) < 0.4:
        return True
    # 超过一半的章节内容 < 100 字
    short_sections = sum(1 for s in sections if len(s["content"]) < 100)
    if short_sections > len(sections) / 2:
        return True
    return False


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
    max_retries = 3
    content = ""
    sections = []

    for attempt in range(max_retries):
        try:
            response = _get_client().chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7 if attempt == 0 else 0.9,
                max_tokens=8000,
            )
            raw_content = response.choices[0].message.content
        except Exception as e:
            if attempt < max_retries - 1:
                continue
            content = f"## 深度分析生成失败\n\n抱歉，AI 深度分析服务暂时不可用。\n\n错误信息：{str(e)}"
            sections = _split_sections(content)
            break

        # 过滤管道
        content = _filter_forbidden_words(raw_content)
        content = _strip_preface(content)
        content = _strip_self_check(content)
        content = _filter_english(content)
        content = _filter_forbidden_words(content)

        sections = _split_sections(content)

        # 质量检查
        if not _is_low_quality(sections, content):
            break  # 质量合格，退出重试

        # 质量不合格，记录日志并重试
        total = sum(len(s["content"]) for s in sections)
        chinese = len(re.findall(r'[\u4e00-\u9fff]', content))
        print(f"[AI] Attempt {attempt+1}/{max_retries} low quality: "
              f"sections={len(sections)}, chars={total}, chinese_ratio={chinese/max(total,1):.2f}",
              flush=True)

        if attempt < max_retries - 1:
            # 重试时在 user prompt 末尾加强调
            user_prompt = user_prompt.replace(
                "\n请确保报告专业、深入、有个性化洞察。",
                "\n请确保报告专业、深入、有个性化洞察。\n\n【重要提醒】请直接输出中文报告正文，不要输出英文大纲、思考笔记或分析思路。每个章节必须有完整的中文段落。"
            )
        else:
            # 最后一次重试仍然失败，使用降级内容
            print("[AI] All retries exhausted, using fallback", flush=True)
            content, sections = _fallback_content(results, profile, content)

    # 检查章节内容质量。如果某个章节过滤后内容太短（< 100 字），
    # 标记 incomplete，前端会显示"重新生成"按钮。
    for sec in sections:
        if len(sec["content"]) < 100:
            sec["incomplete"] = True

    return {
        "detailed_analysis": content,
        "sections": sections,
    }


def _fallback_content(results, profile, original_content):
    """当 AI 多次重试后仍然输出低质量内容时，使用降级方案。
    保留 AI 已生成的有效章节，对缺失或过短的章节用模板补充。"""
    en = results.get("enneagram", {})
    mb = results.get("mbti", {})
    ho = results.get("holland", {})
    ga = results.get("gallup", {})

    en_type = en.get('type_name', '')
    mb_type = mb.get('type', '')
    ho_code = ho.get('code', '')
    ga_domain = GALLUP_DOMAIN_NAMES.get(ga.get('top_domain', ''), ga.get('top_domain', '关系建立'))
    role = profile.get('role', '当前角色')

    templates = {
        "1": (
            f"### 核心特质\n\n"
            f"你的九型主型为 **{en.get('main_type')}号 {en_type}**。"
            f"这一类型的核心特质在于对内在真实性的深度追求。"
            f"你在得分中展现了对多种人格特质的探索欲望，"
            f"这说明你并非单一维度的人，而是具有丰富内在层次的个体。\n\n"
            f"### 内在动力\n\n"
            f"驱动你的核心力量是寻找自我认同的答案。"
            f"你渴望理解自己存在的独特意义，"
            f"并在生活中不断验证和深化这种认知。\n\n"
            f"### 成长方向\n\n"
            f"在保持自我觉察优势的同时，尝试将更多的注意力转向行动和外部世界。"
            f"将内在的丰富感受转化为具体的创造和表达，而非仅停留在思考层面。"
        ),
        "2": (
            f"### 类型定位\n\n"
            f"你的 MBTI 类型为 **{mb_type}**。"
            f"这一类型决定了你处理信息和做决策的独特方式。"
            f"你的认知功能栈赋予你敏锐的直觉和深度的共情能力，"
            f"这在你的{role}角色中既是优势也可能带来挑战。\n\n"
            f"### 互动风格\n\n"
            f"你在人际互动中倾向于建立深层的情感连接，而非表面的社交关系。"
            f"你更关注他人的感受和需求，善于倾听和共情。\n\n"
            f"### 发展建议\n\n"
            f"建议在保持共情优势的同时，培养更多的逻辑分析和系统思考能力。"
            f"在需要做出客观决策的场景中，学会暂时抽离情感因素，用数据和逻辑辅助判断。"
        ),
        "3": (
            f"### 代码解读\n\n"
            f"你的霍兰德职业代码为 **{ho_code}**。"
            f"这个代码组合揭示了你在职业环境中的自然偏好——"
            f"你倾向于在既能发挥创造力又有社会价值的环境中工作。\n\n"
            f"### 适合的职业方向\n\n"
            f"基于你的代码，以下方向值得探索："
            f"产品与用户体验、教育与培训、心理咨询与辅导、"
            f"创意策划与内容创作、人力资源与组织发展。\n\n"
            f"### 发展路径\n\n"
            f"建议从当前{role}出发，逐步拓展到需要创意与人际能力并重的岗位。"
            f"短期可以深耕专业能力，中期拓展跨领域协作经验。"
        ),
        "4": (
            f"### 优势解读\n\n"
            f"你的盖洛普主导领域为 **{ga_domain}**。"
            f"核心主题包括你最为突出的几项才能，"
            f"这些主题在你的日常工作中已经展现出强大的影响力。\n\n"
            f"### 优势发挥\n\n"
            f"你最大的优势在于建立和维护深层人际关系的能力。"
            f"在团队中，你常常是那个能感知他人情绪、化解冲突、促进协作的关键角色。\n\n"
            f"### 补盲建议\n\n"
            f"注意在发挥关系优势的同时，不要忽视执行力和影响力层面的建设。"
            f"可以刻意练习目标设定和进度追踪，确保关系维护转化为实际成果。"
        ),
        "5": (
            f"### 协同点\n\n"
            f"四体系共同指向一个核心画像：你是一个以感受力驱动的创造性人本主义者。"
            f"九型的深度自我探索、MBTI的直觉与共情、霍兰德的艺术与社会兴趣、"
            f"盖洛普的关系优势——这些维度在四套不同的测评框架中"
            f"高度一致地指向同一个方向。\n\n"
            f"### 张力点\n\n"
            f"四体系也存在张力：你丰富的内在感受有时可能与高效执行产生矛盾；"
            f"对深度的追求可能让你忽视广度的价值；"
            f"关系导向的优势在需要果断决策时可能成为犹豫的来源。\n\n"
            f"### 融合洞察\n\n"
            f"你的四体系结果呈现罕见的同频共振。"
            f"建议在{role}中，发挥你连接深度思考与人文关怀的独特优势，"
            f"同时刻意培养执行纪律和影响力，让创造力和共情力落地为可见的成果。"
        ),
    }

    # 尝试从 AI 原始输出中提取有效章节
    existing = {}
    for sec in _split_sections(original_content):
        title = sec["title"]
        if len(sec["content"]) > 150:
            for num in ["1", "2", "3", "4", "5"]:
                if num in title:
                    existing[num] = sec["content"]
                    break

    # 构建最终章节列表
    titles = ["1. 九型人格深度解读", "2. MBTI深度分析",
              "3. 霍兰德职业方向", "4. 盖洛普优势发挥",
              "5. 四体系综合交叉解读"]
    final_sections = []
    parts = []
    for i, num in enumerate(["1", "2", "3", "4", "5"]):
        c = existing.get(num, templates[num])
        title = titles[i]
        final_sections.append({"title": title, "content": c})
        parts.append(f"## {title}\n\n{c}")

    return "\n\n".join(parts), final_sections


def _mock_sections(results, profile):
    """AI_MOCK 模式下的固定章节（结构对齐真实输出，供联调/测试）。"""
    en = results.get("enneagram", {})
    mb = results.get("mbti", {})
    ho = results.get("holland", {})
    ga = results.get("gallup", {})
    sections = [
        {"title": "九型人格深度解读", "content": f"## {en.get('main_type')}号 {en.get('type_name')}\n\n你的九型主型为 **{en.get('main_type')}号 {en.get('type_name')}**。核心特质包括追求卓越、关注效率与形象管理。内在动力源于对成功和认可的渴望，恐惧被否定或被视为失败者。成长方向是学会真实地连接他人，而非仅通过成就获得认可。"},
        {"title": "MBTI深度分析", "content": f"## {mb.get('type')}\n\n你的 MBTI 类型为 **{mb.get('type')}**。认知功能栈以思维和判断为主导，擅长系统性分析和目标导向的执行。互动风格直接高效，偏好结构化的沟通方式。发展建议是培养对他人情感的感知力，在决策中适当融入人文关怀。"},
        {"title": "霍兰德职业方向", "content": f"## {ho.get('code')}\n\n你的霍兰德代码为 **{ho.get('code')}**。基于该代码组合，推荐以下职业方向：\n- 产品经理\n- 项目管理\n- 市场战略\n- 创业运营\n- 数据分析\n- 管理咨询\n这些方向既匹配你的实际型和企业型倾向，也能发挥你在执行和战略方面的优势。"},
        {"title": "盖洛普优势发挥", "content": f"## {ga.get('top_domain')}\n\n主导领域 **{ga.get('top_domain')}**。核心主题包括成就、专注和统筹。优势发挥建议：在目标明确的环境中你能够高效产出，适合担任推动落地的角色。补盲建议：注意在追求效率时不要忽视团队的情感需求，适当放慢节奏倾听不同声音。"},
        {"title": "四体系综合交叉解读", "content": """## 四体系综合交叉解读

### 九型
- 协同信号：核心驱动力与MBTI主导功能方向一致，目标/价值定位清晰，追求卓越的动机与判断型偏好形成正向循环
- 张力提示：单一型态聚焦易忽略其他维度的信号，完美主义倾向可能导致过度自我批判

### MBTI
- 协同信号：认知功能栈与霍兰德偏好的活动方式呼应，思维-判断组合与常规型/研究型兴趣形成高效执行路径
- 张力提示：判断/感知维度过于强势会限制灵活性，在需要快速应变的场景中可能显得僵化

### 霍兰德
- 协同信号：职业兴趣代码与盖洛普主题形成行为落地路径，常规型的结构化偏好为战略思维提供了实施框架
- 张力提示：类型差距在跨领域任务中会暴露短板，艺术型和企业型的低分可能限制创意表达和影响力发挥

### 盖洛普
- 协同信号：优势主题直接放大四体系的执行力或影响力，战略思维领域的强势为所有体系提供了方向感和规划能力
- 张力提示：主题堆叠在某个领域会造成失衡，关系建立和影响力领域的薄弱可能影响团队协作效果

### 融合洞察

四套体系都指向同一类人——你是一个**目标/价值双驱动的整合者**：九型提供动机来源，MBTI 决定信息处理方式，霍兰德定义与环境互动的偏好场域，盖洛普主题则把上述抽象倾向落地为可操作的优势。在保持主航道聚焦的同时，留出 20% 的精力探索张力点指出的盲区，将让你从「单点优势」走向「系统优势」。"""},
    ]

    # 当存在 birth_date 时，添加第 6 章
    if profile.get("birth_date"):
        sections.append({
            "title": "传统易学结合解读",
            "content": '## 命理与心理的呼应\n\n### 当前发展阶段定位\n\n结合您的出生年月日，当前正处于事业上升期，能量场偏向行动与突破。这是建立核心竞争力和拓展影响力的关键阶段。\n\n### 近三年专注方向\n\n建议未来 1-3 年聚焦于专业深度的建立和资源网络的拓展。适合主导创新型项目，将个人能力转化为可复制的系统。\n\n### 阶段性格避坑提醒\n\n当前阶段需注意避免过度自信导致的决策仓促。在高速发展中容易忽略细节和人际维护，建议定期复盘并保持与导师的对话。\n\n### 与四体系交叉验证\n\n九型 8 号的挑战者特质与当前命理阶段的突破能量高度吻合。MBTI 判断型偏好与「事业上升期」的节奏匹配。霍兰德企业型倾向在当前阶段有天然优势。盖洛普执行力领域的强势为这一阶段提供了坚实的行动力基础。'
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
    如果没有找到任何标题，但找到 `---` 分隔符，也截断分隔符之前的内容。
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

    # 如果没有找到任何标题，检查是否有 --- 分隔符
    # AI 有时会先输出思考过程，然后用 --- 分隔，再输出正式报告
    if first_heading_idx is None:
        for i, line in enumerate(lines):
            if line.strip() == '---':
                # 找到分隔符，检查后面是否有实质内容
                after = '\n'.join(lines[i + 1:]).strip()
                if len(after) > 200:  # 确保后面有足够内容
                    return after

    return text


def _strip_self_check(text):
    """
    移除 AI 末尾的自检清单和思考过程。
    Minimax M3 有时在报告结束后附加：
    - 自检清单（"1. ✅ Markdown format" "2. ✅ Simplified Chinese" 等）
    - AI 自我评价（"I think this is good" "Let me check" 等）
    - 重复的报告标题和元文本

    策略：找到第一个自检标记的位置，截断其后的所有内容。
    如果没有自检标记，则移除末尾的纯英文段落和 AI 自评行。
    """
    lines = text.split('\n')

    # 自检清单的标记模式：
    # 1. ✅ 开头的行
    # 2. "I think this is" / "Let me check" / "I should note" 等 AI 自评
    # 3. 末尾重复出现的 "# 心理测评深度解读报告" 等元标题
    self_check_start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        # 检测 ✅ 自检清单行
        if re.match(r'^\d+\.\s*✅', stripped):
            self_check_start = i
            break
        # 检测 AI 自评行（纯英文，无中文）
        if re.match(r'^(I think |I should |Let me |I\'ll |I will |I also |Note that |This is )', stripped, re.IGNORECASE):
            if not re.search(r'[\u4e00-\u9fff]', stripped):
                self_check_start = i
                break
        # 检测 AI 规则笔记行（"Important notes from the rules:" 等）
        if re.match(r'^(Important notes|Key points|Notes from|Reminders?|Rules? to|Guidelines?)', stripped, re.IGNORECASE):
            if not re.search(r'[\u4e00-\u9fff]', stripped):
                self_check_start = i
                break
        # 检测纯英文的要点列表（- No xxx / - Use xxx 等 AI 规则复述）
        if stripped.startswith('- ') and not re.search(r'[\u4e00-\u9fff]', stripped):
            # 检查是否是 AI 规则复述关键词
            if re.search(r'\b(no |don\'t|avoid|use |ensure|direct |must |should |chinese|markdown|format|outline|thinking|self.check|meta text)\b', stripped, re.IGNORECASE):
                self_check_start = i
                break

    if self_check_start is not None:
        # 截断自检清单开始位置之后的所有内容
        lines = lines[:self_check_start]

    # 移除末尾的空行和分割线
    while lines and (not lines[-1].strip() or lines[-1].strip() in ('---', '***', '___')):
        lines.pop()

    return '\n'.join(lines).rstrip()


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
        if re.match(r'^(Here |I\'ll |Let me |Sure,|Below is|This is |The user |Now I |First,|Second,|Let\'s |I will |I need |I should |I think |I also |Given |Since )', stripped, re.IGNORECASE):
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

        # 跳过 AI 自检清单行（✅ 标记 + 英文描述）
        if '✅' in stripped and not has_chinese:
            continue

        # 过滤纯英文段落：行中没有任何中文字符 + 英文单词 > 8 个
        if not has_chinese and not stripped.startswith('#'):
            english_word_count = len(re.findall(r'[a-zA-Z]+', stripped))
            # 排除 MBTI/霍兰德等类型代码行
            is_code_line = bool(re.match(r'^(MBTI|RIASEC|ISTP|ISFP|INTJ|INFJ|ENTP|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ESTP|ESFP|ENTJ|ENFJ|RES|EIS|SIA|ASE|SEC|CSE|IA|SE|RE|RC|RI)\b', stripped))
            if english_word_count > 8 and not is_code_line:
                continue

        # 过滤"半英文"笔记行：中文 < 5 字但英文单词 > 5 个
        # 这类行通常是 AI 的大纲笔记（如 "Focus on Type 4 (个人主义者) as primary type..."）
        if chinese_count < 5 and not stripped.startswith('#'):
            english_word_count = len(re.findall(r'[a-zA-Z]+', stripped))
            if english_word_count > 5:
                # 排除包含中文术语的代码行
                if not re.match(r'^(MBTI|RIASEC|ISTP|ISFP|INTJ|INFJ|ENTP|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ESTP|ESFP|ENTJ|ENFJ|RES|EIS|SIA|ASE|SEC|CSE|IA|SE|RE|RC|RI)\b', stripped):
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
