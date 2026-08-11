#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_new_questions.py — 生成40道新题补充题库
重点补充 Holland R 型（实操/动手/机械/户外）覆盖
"""
import json, re, os

# 加载现有题干用于查重
existing_stems = []
existing_normalized = set()
with open('items.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            q = json.loads(line)
            existing_stems.append(q['stem'])
            # 标准化
            ns = re.sub(r'[，。？！,. ?！]', '', q['stem'])
            ns = re.sub(r'[（(][^）)]*[）)]', '', ns)
            existing_normalized.add(ns)

# 40道新题，重点补 Holland R 型
new_questions = [
    # === work-career (4) ===
    {
        "stem": "工作中遇到设备故障，我的第一反应是",
        "category": "work-career",
        "scale": "forced-choice",
        "options": [
            {"text": "自己拆开看看哪里出了问题", "score": {"enneagram.type8": 1, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "先查手册或搜索解决方案", "score": {"enneagram.type5": 2, "mbti.N": 1, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "叫维修人员来处理", "score": {"enneagram.type9": 1, "mbti.F": 1, "holland.C": 1, "gallup.relationship_building": 1}},
            {"text": "先问同事有没有遇到过类似问题", "score": {"enneagram.type6": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
        ],
        "gallup_themes": ["restorative", "fixer"],
        "applicable_states": ["mid-career", "career-transition", "entrepreneur-stage"],
        "difficulty": 2,
    },
    {
        "stem": "我更喜欢在什么样的环境里办公",
        "category": "work-career",
        "scale": "forced-choice",
        "options": [
            {"text": "能走动、有实操空间的地方", "score": {"enneagram.type7": 1, "mbti.S": 2, "holland.R": 2, "gallup.executing": 1}},
            {"text": "安静的办公室里独立思考", "score": {"enneagram.type5": 2, "mbti.I": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "和人频繁交流的开放空间", "score": {"enneagram.type2": 2, "mbti.E": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "有规则和流程的规范场所", "score": {"enneagram.type1": 2, "mbti.J": 2, "holland.C": 2, "gallup.executing": 1}},
        ],
        "gallup_themes": ["adaptability"],
        "applicable_states": ["career-choice", "mid-career", "career-transition"],
        "difficulty": 2,
    },
    {
        "stem": "团队需要搭建一个展示架，我会",
        "category": "work-career",
        "scale": "forced-choice",
        "options": [
            {"text": "主动拿起工具开始组装", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "先研究说明书再动手", "score": {"enneagram.type5": 2, "mbti.J": 1, "holland.C": 2, "gallup.strategic_thinking": 1}},
            {"text": "指挥别人来做", "score": {"enneagram.type3": 2, "mbti.E": 1, "holland.E": 2, "gallup.influencing": 2}},
            {"text": "在旁边帮忙递工具打下手", "score": {"enneagram.type2": 2, "mbti.F": 1, "holland.S": 1, "gallup.relationship_building": 2}},
        ],
        "gallup_themes": ["achiever", "arranger"],
        "applicable_states": ["entrepreneur-stage", "leadership-growth", "mid-career"],
        "difficulty": 3,
    },
    {
        "stem": "我对使用工具和机械设备的感觉是",
        "category": "work-career",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合我喜欢", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type3": 1, "mbti.S": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type4": 1, "mbti.N": 1, "holland.A": 1}},
            {"text": "完全不符合", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["achiever"],
        "applicable_states": ["career-choice", "career-transition"],
        "difficulty": 2,
        "reverse": False,
    },

    # === learning-cognition (4) ===
    {
        "stem": "学一项新技能时，我最有效的学习方式是",
        "category": "learning-cognition",
        "scale": "forced-choice",
        "options": [
            {"text": "反复练习直到熟练", "score": {"enneagram.type1": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "理解背后的原理和理论", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "看教学视频跟着做", "score": {"enneagram.type3": 1, "mbti.S": 1, "holland.A": 1, "gallup.executing": 1}},
            {"text": "找人一起学互相讨论", "score": {"enneagram.type2": 2, "mbti.E": 1, "holland.S": 2, "gallup.relationship_building": 2}},
        ],
        "gallup_themes": ["learner", "input"],
        "applicable_states": ["study-direction", "fresh-grad", "career-transition"],
        "difficulty": 2,
    },
    {
        "stem": "面对一个复杂的实物模型，我倾向于",
        "category": "learning-cognition",
        "scale": "forced-choice",
        "options": [
            {"text": "直接动手拆解研究", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "先画图分析结构", "score": {"enneagram.type5": 2, "mbti.N": 1, "holland.I": 1, "gallup.strategic_thinking": 2}},
            {"text": "找说明书或图纸来看", "score": {"enneagram.type6": 2, "mbti.J": 2, "holland.C": 2, "gallup.strategic_thinking": 1}},
            {"text": "问老师或专家怎么拆", "score": {"enneagram.type9": 1, "mbti.F": 1, "holland.S": 1, "gallup.relationship_building": 2}},
        ],
        "gallup_themes": ["learner", "restorative"],
        "applicable_states": ["study-direction", "academic-stress", "graduate-school"],
        "difficulty": 3,
    },
    {
        "stem": "我喜欢动手制作或修理东西",
        "category": "learning-cognition",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type3": 1, "mbti.S": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type4": 1, "mbti.N": 1, "holland.A": 1}},
            {"text": "完全不符合", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2}},
        ],
        "gallup_themes": ["achiever", "restorative"],
        "applicable_states": ["self-exploration", "career-choice", "study-direction"],
        "difficulty": 2,
        "reverse": False,
    },
    {
        "stem": "实验课上我通常是",
        "category": "learning-cognition",
        "scale": "forced-choice",
        "options": [
            {"text": "第一个动手操作的人", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "先观察别人怎么做", "score": {"enneagram.type5": 2, "mbti.I": 1, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "记录数据和过程", "score": {"enneagram.type1": 2, "mbti.J": 2, "holland.C": 2, "gallup.executing": 1}},
            {"text": "和搭档一起配合完成", "score": {"enneagram.type2": 2, "mbti.F": 1, "holland.S": 2, "gallup.relationship_building": 2}},
        ],
        "gallup_themes": ["learner", "arranger"],
        "applicable_states": ["academic-stress", "study-direction", "graduate-school"],
        "difficulty": 3,
    },

    # === stress-response (4) ===
    {
        "stem": "压力大时，什么活动最能让我放松",
        "category": "stress-response",
        "scale": "forced-choice",
        "options": [
            {"text": "运动、跑步或做手工", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "看书或独自冥想", "score": {"enneagram.type5": 2, "mbti.I": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "找朋友倾诉", "score": {"enneagram.type2": 2, "mbti.E": 1, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "听音乐或画画", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["adaptability"],
        "applicable_states": ["academic-stress", "mid-career", "life-transition"],
        "difficulty": 2,
    },
    {
        "stem": "紧张的工作之后，我更想",
        "category": "stress-response",
        "scale": "forced-choice",
        "options": [
            {"text": "去户外活动出出汗", "score": {"enneagram.type7": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "在家安静地看剧或读书", "score": {"enneagram.type9": 2, "mbti.I": 2, "holland.A": 1, "gallup.strategic_thinking": 1}},
            {"text": "约朋友聚餐聊天", "score": {"enneagram.type2": 2, "mbti.E": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "做些有创意的手工或写作", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["adaptability"],
        "applicable_states": ["mid-career", "academic-stress", "career-transition"],
        "difficulty": 2,
    },
    {
        "stem": "我觉得手工劳动比脑力劳动更让我有成就感",
        "category": "stress-response",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type3": 1, "mbti.S": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type5": 1, "mbti.N": 1, "holland.I": 1}},
            {"text": "完全不符合", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
        ],
        "gallup_themes": ["achiever"],
        "applicable_states": ["self-exploration", "career-choice"],
        "difficulty": 3,
        "reverse": False,
    },
    {
        "stem": "面对突发状况，我的第一反应是",
        "category": "stress-response",
        "scale": "forced-choice",
        "options": [
            {"text": "立刻采取行动解决", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 1, "gallup.executing": 2}},
            {"text": "先冷静分析原因", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "安抚周围人的情绪", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "按预案流程走", "score": {"enneagram.type1": 2, "mbti.J": 2, "holland.C": 2, "gallup.executing": 1}},
        ],
        "gallup_themes": ["restorative", "arranger"],
        "applicable_states": ["entrepreneur-stage", "leadership-growth", "mid-career"],
        "difficulty": 4,
    },

    # === interpersonal-relationship (4) ===
    {
        "stem": "和朋友一起时，我更倾向于",
        "category": "interpersonal-relationship",
        "scale": "forced-choice",
        "options": [
            {"text": "一起做运动或户外活动", "score": {"enneagram.type7": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "深入交谈分享想法", "score": {"enneagram.type4": 2, "mbti.N": 1, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "一起参加社交聚会", "score": {"enneagram.type2": 2, "mbti.E": 2, "holland.S": 2, "gallup.influencing": 2}},
            {"text": "一起玩策略游戏", "score": {"enneagram.type5": 1, "mbti.T": 2, "holland.I": 1, "gallup.strategic_thinking": 2}},
        ],
        "gallup_themes": ["woo", "relator"],
        "applicable_states": ["self-exploration", "relationship-conflict"],
        "difficulty": 2,
    },
    {
        "stem": "朋友搬新家需要帮忙组装家具，我会",
        "category": "interpersonal-relationship",
        "scale": "forced-choice",
        "options": [
            {"text": "带上工具第一个到", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "帮忙规划布局和设计", "score": {"enneagram.type4": 1, "mbti.N": 2, "holland.A": 2, "gallup.strategic_thinking": 1}},
            {"text": "带点吃的来慰问大家", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "负责记账和分摊费用", "score": {"enneagram.type1": 2, "mbti.T": 1, "holland.C": 2, "gallup.executing": 1}},
        ],
        "gallup_themes": ["relator", "arranger"],
        "applicable_states": ["relationship-conflict", "life-transition"],
        "difficulty": 3,
    },
    {
        "stem": "在人际交往中我更看重",
        "category": "interpersonal-relationship",
        "scale": "forced-choice",
        "options": [
            {"text": "一起做事的默契", "score": {"enneagram.type8": 1, "mbti.S": 2, "holland.R": 1, "gallup.executing": 2}},
            {"text": "思想上的共鸣", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 1, "gallup.strategic_thinking": 1}},
            {"text": "情感的温暖和支持", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "共同的兴趣和话题", "score": {"enneagram.type7": 2, "mbti.E": 1, "holland.S": 1, "gallup.influencing": 1}},
        ],
        "gallup_themes": ["relator", "empathy"],
        "applicable_states": ["self-exploration", "relationship-conflict"],
        "difficulty": 3,
    },
    {
        "stem": "我觉得动手帮别人做事比说安慰话更实在",
        "category": "interpersonal-relationship",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type3": 1, "mbti.S": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2}},
            {"text": "完全不符合", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 2}},
        ],
        "gallup_themes": ["giver", "relator"],
        "applicable_states": ["self-exploration", "relationship-conflict"],
        "difficulty": 3,
        "reverse": False,
    },

    # === decision-making (4) ===
    {
        "stem": "做一个重要决定前，我通常",
        "category": "decision-making",
        "scale": "forced-choice",
        "options": [
            {"text": "先试一试看看效果", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "搜集大量信息深入分析", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "征求身边人的意见", "score": {"enneagram.type2": 1, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "列出利弊清单打分", "score": {"enneagram.type1": 2, "mbti.T": 2, "holland.C": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["analytical", "deliberative"],
        "applicable_states": ["career-choice", "career-transition", "life-transition"],
        "difficulty": 3,
    },
    {
        "stem": "面对两个都不错的选择时，我会",
        "category": "decision-making",
        "scale": "forced-choice",
        "options": [
            {"text": "直接试一个看看", "score": {"enneagram.type7": 2, "mbti.S": 1, "holland.R": 2, "gallup.executing": 2}},
            {"text": "反复思考找到最优解", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "问问家人朋友的建议", "score": {"enneagram.type6": 2, "mbti.F": 2, "holland.S": 1, "gallup.relationship_building": 2}},
            {"text": "按经验和惯例来", "score": {"enneagram.type1": 2, "mbti.J": 2, "holland.C": 2, "gallup.executing": 1}},
        ],
        "gallup_themes": ["deliberative"],
        "applicable_states": ["career-choice", "study-direction", "life-transition"],
        "difficulty": 3,
    },
    {
        "stem": "我喜欢需要动手操作的决策任务",
        "category": "decision-making",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type3": 1, "mbti.S": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type9": 1, "mbti.N": 1, "holland.I": 1}},
            {"text": "完全不符合", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.A": 2}},
        ],
        "gallup_themes": ["achiever"],
        "applicable_states": ["career-choice", "entrepreneur-stage"],
        "difficulty": 3,
        "reverse": False,
    },
    {
        "stem": "选择项目方案时，我更倾向",
        "category": "decision-making",
        "scale": "forced-choice",
        "options": [
            {"text": "可落地的实物方案", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "创新性强的理论方案", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 2, "gallup.strategic_thinking": 2}},
            {"text": "大家都认可的合作方案", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "风险可控的稳妥方案", "score": {"enneagram.type6": 2, "mbti.J": 2, "holland.C": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["arranger", "deliberative"],
        "applicable_states": ["entrepreneur-stage", "leadership-growth", "mid-career"],
        "difficulty": 4,
    },

    # === motivation-value (4) ===
    {
        "stem": "什么最能给我带来成就感",
        "category": "motivation-value",
        "scale": "forced-choice",
        "options": [
            {"text": "亲手完成一件实物作品", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "解决一个复杂的理论问题", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "帮助他人成长和改变", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "获得外界的认可和赞赏", "score": {"enneagram.type3": 2, "mbti.E": 2, "holland.E": 2, "gallup.influencing": 2}},
        ],
        "gallup_themes": ["achiever", "significance"],
        "applicable_states": ["self-exploration", "career-choice", "leadership-growth"],
        "difficulty": 2,
    },
    {
        "stem": "我认为最有价值的工作是",
        "category": "motivation-value",
        "scale": "forced-choice",
        "options": [
            {"text": "能看得见实际成果的", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "能推动知识进步的", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "能帮助到他人的", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "能展现个人才华的", "score": {"enneagram.type4": 2, "mbti.N": 1, "holland.A": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["significance", "belief"],
        "applicable_states": ["career-choice", "self-exploration", "career-transition"],
        "difficulty": 3,
    },
    {
        "stem": "我最享受的时刻是",
        "category": "motivation-value",
        "scale": "forced-choice",
        "options": [
            {"text": "在户外用双手创造东西", "score": {"enneagram.type7": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "在书房里深入思考", "score": {"enneagram.type5": 2, "mbti.I": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "和朋友在一起聊天", "score": {"enneagram.type2": 2, "mbti.E": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "独自创作艺术作品", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["achiever"],
        "applicable_states": ["self-exploration", "life-transition"],
        "difficulty": 2,
    },
    {
        "stem": "比起讨论方案我更喜欢直接动手干",
        "category": "motivation-value",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type7": 1, "mbti.S": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type5": 1, "mbti.N": 1, "holland.I": 1}},
            {"text": "完全不符合", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
        ],
        "gallup_themes": ["achiever", "activator"],
        "applicable_states": ["entrepreneur-stage", "career-choice", "mid-career"],
        "difficulty": 2,
        "reverse": False,
    },

    # === emotion-self (4) ===
    {
        "stem": "心情低落时，做什么最能让我好转",
        "category": "emotion-self",
        "scale": "forced-choice",
        "options": [
            {"text": "去做运动或手工转移注意", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "独处思考理清情绪", "score": {"enneagram.type4": 2, "mbti.I": 2, "holland.A": 2, "gallup.strategic_thinking": 1}},
            {"text": "找信任的人倾诉", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "制定计划让自己忙起来", "score": {"enneagram.type3": 2, "mbti.J": 2, "holland.C": 2, "gallup.executing": 2}},
        ],
        "gallup_themes": ["adaptability", "empathy"],
        "applicable_states": ["self-exploration", "life-transition", "academic-stress"],
        "difficulty": 2,
    },
    {
        "stem": "我觉得自己的情绪状态受身体活动影响很大",
        "category": "emotion-self",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合", "score": {"enneagram.type7": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type8": 1, "mbti.S": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type5": 1, "mbti.N": 1, "holland.I": 1}},
            {"text": "完全不符合", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 2}},
        ],
        "gallup_themes": ["adaptability"],
        "applicable_states": ["self-exploration", "life-transition"],
        "difficulty": 3,
        "reverse": False,
    },
    {
        "stem": "当我感到焦虑时我会通过体力活动来释放",
        "category": "emotion-self",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type7": 1, "mbti.S": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type9": 1, "mbti.I": 1, "holland.S": 1}},
            {"text": "完全不符合", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["adaptability"],
        "applicable_states": ["academic-stress", "mid-career", "life-transition"],
        "difficulty": 3,
        "reverse": False,
    },
    {
        "stem": "独处时我更喜欢做什么来调节心情",
        "category": "emotion-self",
        "scale": "forced-choice",
        "options": [
            {"text": "修理东西或做手工", "score": {"enneagram.type8": 1, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "写日记或听音乐", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 2, "gallup.strategic_thinking": 1}},
            {"text": "整理房间或打扫卫生", "score": {"enneagram.type1": 2, "mbti.J": 2, "holland.C": 2, "gallup.executing": 1}},
            {"text": "规划未来的目标", "score": {"enneagram.type3": 2, "mbti.N": 1, "holland.E": 2, "gallup.strategic_thinking": 2}},
        ],
        "gallup_themes": ["adaptability", "belief"],
        "applicable_states": ["self-exploration", "life-transition"],
        "difficulty": 2,
    },

    # === action-habit (4) ===
    {
        "stem": "我的周末更可能是这样的",
        "category": "action-habit",
        "scale": "forced-choice",
        "options": [
            {"text": "户外徒步骑行或运动", "score": {"enneagram.type7": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "在家看书看纪录片", "score": {"enneagram.type5": 2, "mbti.I": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "和朋友逛街聚餐", "score": {"enneagram.type2": 2, "mbti.E": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "在家画画写东西做手工", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["adaptability"],
        "applicable_states": ["self-exploration", "mid-career", "life-transition"],
        "difficulty": 2,
    },
    {
        "stem": "整理房间时我通常的做法是",
        "category": "action-habit",
        "scale": "forced-choice",
        "options": [
            {"text": "动手把东西全部搬出来重新摆", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "先画平面图想好布局", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 1, "gallup.strategic_thinking": 2}},
            {"text": "找个朋友一起整理", "score": {"enneagram.type2": 2, "mbti.E": 1, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "按固定流程逐步归位", "score": {"enneagram.type1": 2, "mbti.J": 2, "holland.C": 2, "gallup.executing": 1}},
        ],
        "gallup_themes": ["arranger", "focus"],
        "applicable_states": ["life-transition", "self-exploration"],
        "difficulty": 2,
    },
    {
        "stem": "比起计划我更喜欢直接行动",
        "category": "action-habit",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type7": 1, "mbti.P": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type6": 1, "mbti.J": 1, "holland.C": 1}},
            {"text": "完全不符合", "score": {"enneagram.type1": 2, "mbti.J": 2, "holland.C": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["activator"],
        "applicable_states": ["entrepreneur-stage", "career-choice", "fresh-grad"],
        "difficulty": 2,
        "reverse": False,
    },
    {
        "stem": "面对一件需要动手的事我会毫不犹豫地开始",
        "category": "action-habit",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type7": 1, "mbti.S": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type6": 1, "mbti.J": 1, "holland.C": 1}},
            {"text": "完全不符合", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
        ],
        "gallup_themes": ["activator", "achiever"],
        "applicable_states": ["entrepreneur-stage", "career-choice"],
        "difficulty": 3,
        "reverse": False,
    },

    # === future-vision (4) ===
    {
        "stem": "我理想的工作场所是",
        "category": "future-vision",
        "scale": "forced-choice",
        "options": [
            {"text": "车间工厂或户外工地", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "实验室或研究院", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "学校医院或社区中心", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "工作室或画廊", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["significance", "belief"],
        "applicable_states": ["career-choice", "study-direction", "fresh-grad"],
        "difficulty": 2,
    },
    {
        "stem": "五年后我希望自己",
        "category": "future-vision",
        "scale": "forced-choice",
        "options": [
            {"text": "经营一家实体工作室", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "在研究领域有突破成果", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "成为团队的精神支柱", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "创办有影响力的品牌", "score": {"enneagram.type3": 2, "mbti.E": 2, "holland.E": 2, "gallup.influencing": 2}},
        ],
        "gallup_themes": ["significance", "vision"],
        "applicable_states": ["career-choice", "study-direction", "entrepreneur-stage"],
        "difficulty": 3,
    },
    {
        "stem": "如果可以自由选择我会从事需要动手的创造工作",
        "category": "future-vision",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合", "score": {"enneagram.type7": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type8": 1, "mbti.S": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type6": 1, "mbti.J": 1, "holland.C": 1}},
            {"text": "完全不符合", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 2}},
        ],
        "gallup_themes": ["vision", "belief"],
        "applicable_states": ["career-choice", "self-exploration", "study-direction"],
        "difficulty": 3,
        "reverse": False,
    },
    {
        "stem": "我认为未来最有价值的能力是",
        "category": "future-vision",
        "scale": "forced-choice",
        "options": [
            {"text": "动手实操和解决实际问题的能力", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "深度思考和跨领域分析的能力", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "共情和联结他人的能力", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "创意表达和审美设计的能力", "score": {"enneagram.type4": 2, "mbti.N": 2, "holland.A": 2, "gallup.strategic_thinking": 1}},
        ],
        "gallup_themes": ["vision", "futuristic"],
        "applicable_states": ["career-choice", "leadership-growth", "entrepreneur-stage"],
        "difficulty": 4,
    },

    # === conflict-choice (4) ===
    {
        "stem": "和别人发生分歧时我通常",
        "category": "conflict-choice",
        "scale": "forced-choice",
        "options": [
            {"text": "用行动证明自己是对的", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "用逻辑和证据说服对方", "score": {"enneagram.type5": 2, "mbti.T": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "体谅对方寻找折中方案", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "退让避免正面冲突", "score": {"enneagram.type9": 2, "mbti.I": 1, "holland.S": 1, "gallup.relationship_building": 1}},
        ],
        "gallup_themes": ["harmony", "competition"],
        "applicable_states": ["relationship-conflict", "leadership-growth", "mid-career"],
        "difficulty": 3,
    },
    {
        "stem": "团队意见不统一时我会",
        "category": "conflict-choice",
        "scale": "forced-choice",
        "options": [
            {"text": "直接动手做出个原型来", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "提议先做调研再决定", "score": {"enneagram.type5": 2, "mbti.N": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "逐个沟通了解大家想法", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "投票走流程", "score": {"enneagram.type1": 2, "mbti.J": 2, "holland.C": 2, "gallup.executing": 1}},
        ],
        "gallup_themes": ["harmony", "arranger"],
        "applicable_states": ["leadership-growth", "entrepreneur-stage", "mid-career"],
        "difficulty": 4,
    },
    {
        "stem": "面对冲突我倾向于用行动而非言语来化解",
        "category": "conflict-choice",
        "scale": "likert-4",
        "options": [
            {"text": "非常符合", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "比较符合", "score": {"enneagram.type7": 1, "mbti.S": 1, "holland.R": 1}},
            {"text": "不太符合", "score": {"enneagram.type2": 1, "mbti.F": 1, "holland.S": 1}},
            {"text": "完全不符合", "score": {"enneagram.type9": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
        ],
        "gallup_themes": ["harmony"],
        "applicable_states": ["relationship-conflict", "leadership-growth"],
        "difficulty": 3,
        "reverse": False,
    },
    {
        "stem": "在意见对立时我最看重的是",
        "category": "conflict-choice",
        "scale": "forced-choice",
        "options": [
            {"text": "实际效果说了算", "score": {"enneagram.type8": 2, "mbti.S": 2, "holland.R": 2, "gallup.executing": 2}},
            {"text": "谁的逻辑更严密", "score": {"enneagram.type5": 2, "mbti.T": 2, "holland.I": 2, "gallup.strategic_thinking": 2}},
            {"text": "大家是否都能接受", "score": {"enneagram.type2": 2, "mbti.F": 2, "holland.S": 2, "gallup.relationship_building": 2}},
            {"text": "是否符合既定规则", "score": {"enneagram.type1": 2, "mbti.J": 2, "holland.C": 2, "gallup.executing": 1}},
        ],
        "gallup_themes": ["harmony", "competition"],
        "applicable_states": ["leadership-growth", "relationship-conflict", "mid-career"],
        "difficulty": 4,
    },
]

# 验证无重复
dupes_found = 0
for nq in new_questions:
    ns = re.sub(r'[，。？！,. ?！]', '', nq['stem'])
    ns = re.sub(r'[（(][^）)]*[）)]', '', ns)
    if ns in existing_normalized:
        print(f"DUPE FOUND: {nq['stem']}")
        dupes_found += 1
    existing_normalized.add(ns)

# 新题内部查重
for i in range(len(new_questions)):
    ns_i = re.sub(r'[，。？！,. ?！]', '', new_questions[i]['stem'])
    for j in range(i+1, len(new_questions)):
        ns_j = re.sub(r'[，。？！,. ?！]', '', new_questions[j]['stem'])
        if ns_i == ns_j:
            print(f"INTERNAL DUPE: {new_questions[i]['stem']} <-> {new_questions[j]['stem']}")
            dupes_found += 1

print(f"\nNew questions: {len(new_questions)}")
print(f"Duplicates found: {dupes_found}")

# 分配 ID
for i, q in enumerate(new_questions):
    q['id'] = f"Q{1461+i:04d}"
    q['systems'] = ["enneagram", "mbti", "holland", "gallup"]
    q.setdefault('reverse', False)

# 追加到题库
with open('items.jsonl', 'a', encoding='utf-8') as f:
    for q in new_questions:
        f.write(json.dumps(q, ensure_ascii=False) + '\n')

print(f"Appended {len(new_questions)} new questions (Q1461-Q{1460+len(new_questions)})")
