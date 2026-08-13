# -*- coding: utf-8 -*-
"""questions_age_multidim.py — 120道新题定义
A. 家长视角(30) B. 青少年(25) C. 新量表(25) D. 四体系多维度(40)
每题4体系8+维度，不与现有2000题重复
"""

def fc(stem, cat, opts, themes, states, diff, notes="", rev=False):
    """forced-choice快捷构造"""
    return {"stem":stem,"category":cat,"scale":"forced-choice","options":opts,
            "gallup_themes":themes,"applicable_states":states,"difficulty":diff,
            "notes":notes,"reverse":rev}

def l5(stem, cat, opts, themes, states, diff, notes="", rev=False):
    return {"stem":stem,"category":cat,"scale":"likert-5","options":opts,
            "gallup_themes":themes,"applicable_states":states,"difficulty":diff,
            "notes":notes,"reverse":rev}

def l7(stem, cat, opts, themes, states, diff, notes="", rev=False):
    return {"stem":stem,"category":cat,"scale":"likert-7","options":opts,
            "gallup_themes":themes,"applicable_states":states,"difficulty":diff,
            "notes":notes,"reverse":rev}

def rk(stem, cat, opts, themes, states, diff, notes=""):
    return {"stem":stem,"category":cat,"scale":"ranking","options":opts,
            "gallup_themes":themes,"applicable_states":states,"difficulty":diff,
            "notes":notes}

# s = score快捷
def s(*pairs):
    return dict(pairs)

NEW_QUESTIONS = [

# ═══════════════════════════════════════════════════
# A. 家长视角题目（30题）
# ═══════════════════════════════════════════════════

# A1. action-habit（5题，当前仅1题）
fc("孩子做作业拖拉时，我通常","action-habit",[
    {"text":"坐在旁边盯着直到写完","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"定好时间让他自己安排","score":s(("enneagram.type8",1),("mbti.T",2),("holland.E",1),("gallup.executing",1))},
    {"text":"不断提醒但不太强制","score":s(("enneagram.type6",2),("mbti.F",1),("holland.S",2),("gallup.relationship_building",1))},
    {"text":"觉得迟早会自己开窍","score":s(("enneagram.type9",2),("mbti.P",2),("holland.A",1))},
],["discipline","responsibility","developer"],["parenting-teen","self-exploration","life-transition"],2,"家长·行动"),

fc("周末陪孩子的时间，我倾向","action-habit",[
    {"text":"安排满满的学习和活动","score":s(("enneagram.type3",2),("mbti.J",2),("holland.E",2),("gallup.executing",2))},
    {"text":"带孩子户外运动或动手做东西","score":s(("enneagram.type7",2),("mbti.S",2),("holland.R",2),("gallup.executing",1))},
    {"text":"在家看书聊天，随意安排","score":s(("enneagram.type9",2),("mbti.I",1),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"让孩子自己决定做什么","score":s(("enneagram.type5",1),("mbti.P",2),("holland.I",1),("gallup.strategic_thinking",1))},
],["arranger","developer","adaptability"],["parenting-teen","self-exploration"],2,"家长·行动·含R"),

l5("我给孩子制定规则后，执行力度","action-habit",[
    {"text":"非常严格，说到做到","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"比较严格","score":s(("enneagram.type1",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"一般，看情况","score":s(("enneagram.type6",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"比较灵活","score":s(("enneagram.type7",1),("mbti.P",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"很灵活，几乎不强制","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["discipline","consistency","belief"],["parenting-teen","self-exploration","life-transition"],3,"家长·行动·likert-5"),

fc("孩子兴趣班的选择，我更倾向","action-habit",[
    {"text":"选能培养实用技能的班","score":s(("enneagram.type3",2),("mbti.S",2),("holland.C",2),("gallup.executing",2))},
    {"text":"选能发挥创造力的班","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"选能锻炼身体的运动班","score":s(("enneagram.type8",2),("mbti.S",1),("holland.R",2),("gallup.executing",2))},
    {"text":"让孩子自己挑感兴趣的","score":s(("enneagram.type9",1),("mbti.P",2),("holland.S",1),("gallup.relationship_building",1))},
],["developer","individualization","maximizer"],["parenting-teen","self-exploration"],2,"家长·行动·含R"),

l5("面对孩子的日常起居，我的管理","action-habit",[
    {"text":"事无巨细全部管到","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"管大部分，放一些","score":s(("enneagram.type6",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"管一半放一半","score":s(("enneagram.type3",1),("mbti.T",1),("holland.S",1),("gallup.strategic_thinking",1))},
    {"text":"只管关键的事","score":s(("enneagram.type5",1),("mbti.T",2),("holland.I",1),("gallup.strategic_thinking",2))},
    {"text":"几乎不管，让孩子自理","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2))},
],["arranger","discipline","adaptability"],["parenting-teen","life-transition"],3,"家长·行动·likert-5"),

# A2. work-career（4题）
l7("兼顾工作和陪伴孩子，我觉得","work-career",[
    {"text":"完全做得到，游刃有余","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.executing",2))},
    {"text":"大部分时候可以","score":s(("enneagram.type3",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"勉强平衡","score":s(("enneagram.type1",1),("mbti.T",1),("holland.S",1),("gallup.strategic_thinking",1))},
    {"text":"有点吃力","score":s(("enneagram.type6",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"经常顾此失彼","score":s(("enneagram.type4",1),("mbti.P",1),("holland.A",1))},
    {"text":"很难兼顾","score":s(("enneagram.type6",2),("mbti.I",1),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"完全做不到","score":s(("enneagram.type9",2),("mbti.I",2),("holland.A",2))},
],["arranger","responsibility","harmony"],["parenting-teen","mid-career","life-transition"],3,"家长·工作·likert-7"),

fc("孩子问我的工作是什么，我会","work-career",[
    {"text":"详细讲解，带他来公司参观","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"用简单比喻让他理解","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"让他自己长大后去探索","score":s(("enneagram.type5",2),("mbti.N",1),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"觉得没必要跟孩子讲","score":s(("enneagram.type9",1),("mbti.I",2),("holland.C",1))},
],["communication","developer","connectedness"],["parenting-teen","mid-career"],2,"家长·工作"),

fc("如果孩子想从事和我一样的职业","work-career",[
    {"text":"全力支持，可以铺路","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"支持但让他先想清楚","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",1),("gallup.strategic_thinking",2))},
    {"text":"建议他多试几个方向","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"希望他走不同的路","score":s(("enneagram.type4",2),("mbti.N",1),("holland.A",2),("gallup.influencing",1))},
],["developer","maximizer","futuristic"],["parenting-teen","career-choice","mid-career"],3,"家长·工作"),

l5("我在职场角色对家庭教育的影响","work-career",[
    {"text":"非常大，正面影响","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"比较大，偏正面","score":s(("enneagram.type2",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"一般，好坏都有","score":s(("enneagram.type6",1),("mbti.T",1),("holland.C",1),("gallup.strategic_thinking",1))},
    {"text":"比较大，偏负面","score":s(("enneagram.type4",1),("mbti.I",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"很大，负面影响","score":s(("enneagram.type9",2),("mbti.I",2),("holland.S",2),("gallup.relationship_building",1))},
],["responsibility","belief","connectedness"],["parenting-teen","mid-career","leadership-growth"],4,"家长·工作·likert-5"),

# A3. learning-cognition（4题）
fc("帮孩子选课外书时，我优先考虑","learning-cognition",[
    {"text":"知识性强的科普百科","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"故事性强的文学小说","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"实操性强的手工实验","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"教做人道理的传记","score":s(("enneagram.type1",2),("mbti.F",1),("holland.S",2),("gallup.relationship_building",2))},
],["input","learner","developer"],["parenting-teen","study-direction","self-exploration"],2,"家长·学习·含R"),

fc("孩子成绩波动时，我的分析方式","learning-cognition",[
    {"text":"找原因，列计划，系统解决","score":s(("enneagram.type1",2),("mbti.T",2),("holland.C",2),("gallup.executing",2))},
    {"text":"和老师沟通了解情况","score":s(("enneagram.type6",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"观察孩子的状态和情绪","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"相信孩子自己能调整","score":s(("enneagram.type7",1),("mbti.N",2),("holland.A",1),("gallup.strategic_thinking",2))},
],["analytical","restorative","individualization"],["parenting-teen","academic-stress","study-direction"],3,"家长·学习"),

rk("我觉得最适合孩子的学习方式","learning-cognition",[
    {"text":"跟着老师系统学","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"自己看书摸索","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"和同学讨论着学","score":s(("enneagram.type2",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"动手实践中学","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
],["learner","input","ideation"],["parenting-teen","study-direction","academic-stress"],3,"家长·学习·ranking·含R"),

fc("孩子问到我也不懂的问题，我会","learning-cognition",[
    {"text":"一起查资料找答案","score":s(("enneagram.type5",2),("mbti.N",1),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"鼓励他问老师或同学","score":s(("enneagram.type2",2),("mbti.F",1),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"让他自己想办法解决","score":s(("enneagram.type8",1),("mbti.T",2),("holland.E",2),("gallup.executing",2))},
    {"text":"承认不懂，一起探索","score":s(("enneagram.type9",2),("mbti.P",2),("holland.A",1),("gallup.strategic_thinking",1))},
],["learner","input","developer"],["parenting-teen","study-direction","self-exploration"],2,"家长·学习"),

# A4. decision-making（4题）
fc("孩子想放弃坚持多年的特长，我会","decision-making",[
    {"text":"坚决不同意，坚持才有收获","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"了解原因后帮他权衡","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"尊重他的选择","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"心疼但支持他的决定","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
],["deliberative","responsibility","developer"],["parenting-teen","life-transition","self-exploration"],3,"家长·决策"),

rk("给孩子选学校时，我最看重","decision-making",[
    {"text":"升学率和成绩排名","score":s(("enneagram.type3",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"师资和教学理念","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"校风和同学氛围","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"离家近和硬件好","score":s(("enneagram.type9",2),("mbti.S",2),("holland.R",1),("gallup.strategic_thinking",1))},
],["analytical","deliberative","focus"],["parenting-teen","study-direction","study-abroad"],3,"家长·决策·ranking"),

fc("家里大事需要决策时，我和孩子","decision-making",[
    {"text":"我来决定，孩子执行","score":s(("enneagram.type8",2),("mbti.T",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"一起讨论，最终我拍板","score":s(("enneagram.type3",2),("mbti.E",1),("holland.E",2),("gallup.influencing",1))},
    {"text":"一起讨论，尊重孩子意见","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"让孩子参与决策过程","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["command","harmony","includer"],["parenting-teen","life-transition","self-exploration"],3,"家长·决策"),

l5("面对孩子升学方向选择，我倾向","decision-making",[
    {"text":"完全按我的规划走","score":s(("enneagram.type8",2),("mbti.J",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"偏我的意见为主","score":s(("enneagram.type1",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"各占一半商量着来","score":s(("enneagram.type6",1),("mbti.T",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"偏孩子的意愿为主","score":s(("enneagram.type2",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",2))},
    {"text":"完全尊重孩子的选择","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["deliberative","individualization","developer"],["parenting-teen","study-direction","career-choice"],3,"家长·决策·likert-5"),

# A5. conflict-choice（3题）
fc("孩子和老师发生矛盾时，我会","conflict-choice",[
    {"text":"先找老师了解全貌","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"直接维护孩子","score":s(("enneagram.type8",2),("mbti.F",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"让孩子自己处理","score":s(("enneagram.type7",1),("mbti.P",2),("holland.A",1),("gallup.executing",1))},
    {"text":"两边调和，找平衡点","score":s(("enneagram.type9",2),("mbti.F",1),("holland.S",2),("gallup.relationship_building",2))},
],["harmony","restorative","empathy"],["parenting-teen","relationship-conflict"],3,"家长·冲突"),

fc("孩子要买昂贵东西，预算紧张时","conflict-choice",[
    {"text":"咬咬牙也要满足","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"讲清家庭情况，拒绝","score":s(("enneagram.type1",2),("mbti.T",2),("holland.C",2),("gallup.executing",2))},
    {"text":"设置条件，达成后买","score":s(("enneagram.type3",2),("mbti.J",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"让他自己攒零花钱买","score":s(("enneagram.type5",2),("mbti.T",1),("holland.C",2),("gallup.strategic_thinking",2))},
],["responsibility","deliberative","consistency"],["parenting-teen","life-transition"],3,"家长·冲突"),

fc("教育理念和家人不一致时，我","conflict-choice",[
    {"text":"坚持自己的方式","score":s(("enneagram.type8",2),("mbti.T",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"妥协，家和万事兴","score":s(("enneagram.type9",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"找第三方专家来评判","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"按各自方式，互不干涉","score":s(("enneagram.type4",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["harmony","belief","command"],["parenting-teen","relationship-conflict","life-transition"],4,"家长·冲突"),

# A6. future-vision（3题）
rk("我对孩子最大的期望是","future-vision",[
    {"text":"事业有成，经济独立","score":s(("enneagram.type3",2),("mbti.J",2),("holland.E",2),("gallup.executing",2))},
    {"text":"身心健康，快乐生活","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"找到热爱的事业","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"有独立思考和判断力","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
],["futuristic","developer","maximizer"],["parenting-teen","self-exploration","life-transition"],3,"家长·未来·ranking"),

fc("十年后我希望和孩子的关系是","future-vision",[
    {"text":"像朋友一样无话不谈","score":s(("enneagram.type7",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"各自独立但互相支持","score":s(("enneagram.type5",2),("mbti.I",1),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"保持亲密但有边界","score":s(("enneagram.type1",2),("mbti.J",1),("holland.C",2),("gallup.executing",1))},
    {"text":"他能照顾好自己就行","score":s(("enneagram.type9",2),("mbti.P",2),("holland.S",1),("gallup.strategic_thinking",1))},
],["relator","futuristic","connectedness"],["parenting-teen","self-exploration","life-transition"],4,"家长·未来"),

fc("面对AI时代的教育变革，我","future-vision",[
    {"text":"让孩子尽早学编程和AI","score":s(("enneagram.type3",2),("mbti.J",2),("holland.I",2),("gallup.executing",2))},
    {"text":"更注重培养创造力","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"关注人际沟通等软实力","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"让孩子多动手做实物","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
],["futuristic","strategic","learner"],["parenting-teen","study-direction","career-choice"],4,"家长·未来·含R"),

# A7. motivation-value（2题）
fc("让孩子学特长最核心的动机是","motivation-value",[
    {"text":"升学加分，竞争力","score":s(("enneagram.type3",2),("mbti.J",2),("holland.E",2),("gallup.executing",2))},
    {"text":"陶冶情操，全面发展","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"发现天赋，找到热爱","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"培养毅力和坚持","score":s(("enneagram.type1",2),("mbti.T",1),("holland.C",2),("gallup.executing",2))},
],["maximizer","developer","belief"],["parenting-teen","study-direction","self-exploration"],3,"家长·动机"),

rk("我认为家庭教育最重要的是","motivation-value",[
    {"text":"培养好习惯和自律","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"建立亲密的亲子关系","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"激发好奇心和学习欲","score":s(("enneagram.type7",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"锻炼独立生存能力","score":s(("enneagram.type8",2),("mbti.T",2),("holland.R",2),("gallup.executing",2))},
],["belief","responsibility","developer"],["parenting-teen","self-exploration","life-transition"],4,"家长·动机·ranking·含R"),

# A8. interpersonal-relationship（2题）
fc("孩子在社交中被排挤时，我会","interpersonal-relationship",[
    {"text":"教他主动融入集体的方法","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"倾听他的感受，先安慰","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"帮他分析问题出在哪","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"找对方家长沟通","score":s(("enneagram.type8",2),("mbti.E",1),("holland.E",2),("gallup.influencing",2))},
],["empathy","relator","harmony"],["parenting-teen","relationship-conflict"],3,"家长·人际"),

fc("其他家长炫耀孩子成绩时，我","interpersonal-relationship",[
    {"text":"也聊聊自己孩子的亮点","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"不比较，每个孩子不一样","score":s(("enneagram.type4",2),("mbti.N",1),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"附和几句，不当回事","score":s(("enneagram.type9",2),("mbti.F",1),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"回去督促孩子加油","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
],["significance","individualization","harmony"],["parenting-teen","relationship-conflict"],3,"家长·人际"),

# A9. stress-response（2题）
fc("辅导孩子作业让我崩溃时，我","stress-response",[
    {"text":"先离开冷静一下再回来","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",1),("gallup.strategic_thinking",2))},
    {"text":"深呼吸，告诉自己要耐心","score":s(("enneagram.type9",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"换个人来辅导","score":s(("enneagram.type7",1),("mbti.P",2),("holland.S",1),("gallup.strategic_thinking",1))},
    {"text":"直接发火然后后悔","score":s(("enneagram.type8",2),("mbti.F",1),("holland.E",2),("gallup.influencing",1))},
],["adaptability","empathy","self-assurance"],["parenting-teen","academic-stress"],2,"家长·压力"),

l5("面对孩子升学带来的焦虑，我","stress-response",[
    {"text":"完全没有，心态很好","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"偶尔有些焦虑","score":s(("enneagram.type3",1),("mbti.J",1),("holland.E",1),("gallup.executing",1))},
    {"text":"经常感到焦虑","score":s(("enneagram.type6",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"大部分时间在焦虑","score":s(("enneagram.type6",2),("mbti.J",1),("holland.C",2),("gallup.executing",1))},
    {"text":"焦虑到影响睡眠","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2))},
],["adaptability","positivity","empathy"],["parenting-teen","academic-stress","life-transition"],3,"家长·压力·likert-5"),

# A10. emotion-self（1题）
l7("我对自己的养育方式是否正确","emotion-self",[
    {"text":"非常确信自己做对了","score":s(("enneagram.type8",2),("mbti.T",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"大部分时候确信","score":s(("enneagram.type3",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"偏向确信","score":s(("enneagram.type2",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"说不清，一半一半","score":s(("enneagram.type6",1),("mbti.T",1),("holland.S",1),("gallup.strategic_thinking",1))},
    {"text":"偏向怀疑","score":s(("enneagram.type4",1),("mbti.N",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"经常怀疑自己","score":s(("enneagram.type6",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",1))},
    {"text":"几乎总在自我否定","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2))},
],["self-assurance","belief","responsibility"],["parenting-teen","self-exploration","life-transition"],4,"家长·情绪·likert-7"),

# ═══════════════════════════════════════════════════
# B. 青少年专属题目（25题）
# ═══════════════════════════════════════════════════

# B1. learning-cognition（5题）
fc("上课听不懂的时候，我通常","learning-cognition",[
    {"text":"课后自己看书搞懂","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"下课追着老师问","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.executing",2))},
    {"text":"找同学讨论请教","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"先放着，等以后再说","score":s(("enneagram.type9",2),("mbti.P",2),("holland.A",1))},
],["learner","input","restorative"],["academic-stress","study-direction"],2,"青少年·学习"),

fc("考前复习我更倾向哪种方式","learning-cognition",[
    {"text":"按计划系统过一遍","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"做模拟题查漏补缺","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"和同学互相提问","score":s(("enneagram.type2",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"临时抱佛脚冲刺","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2))},
],["discipline","focus","learner"],["academic-stress","study-direction"],2,"青少年·学习"),

fc("小组作业里我通常担任的角色","learning-cognition",[
    {"text":"组长，分配任务推进","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"负责查资料做研究","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"负责做PPT和展示","score":s(("enneagram.type7",2),("mbti.E",1),("holland.A",2),("gallup.influencing",1))},
    {"text":"负责协调和润滑关系","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
],["arranger","communication","harmony"],["academic-stress","study-direction","self-exploration"],2,"青少年·学习"),

l5("面对不喜欢的科目，我的策略","learning-cognition",[
    {"text":"迎难而上，花更多时间","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"找方法让它变得有趣","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"保证及格就行","score":s(("enneagram.type3",1),("mbti.T",1),("holland.E",1),("gallup.executing",1))},
    {"text":"只学考试要考的部分","score":s(("enneagram.type6",1),("mbti.S",1),("holland.C",1),("gallup.strategic_thinking",1))},
    {"text":"尽量逃避","score":s(("enneagram.type9",2),("mbti.P",2),("holland.A",2))},
],["focus","learner","discipline"],["academic-stress","study-direction"],2,"青少年·学习·likert-5"),

fc("动手实验和理论推导，我更喜欢","learning-cognition",[
    {"text":"动手做实验看结果","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"从理论推导到结论","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"两者结合最好","score":s(("enneagram.type3",2),("mbti.T",1),("holland.C",2),("gallup.executing",1))},
    {"text":"听老师讲就行","score":s(("enneagram.type9",2),("mbti.F",1),("holland.S",2),("gallup.relationship_building",1))},
],["learner","input","achiever"],["academic-stress","study-direction","career-choice"],2,"青少年·学习·含R"),

# B2. interpersonal-relationship（5题）
fc("班里同学拉帮结派时，我会","interpersonal-relationship",[
    {"text":"加入人多热闹的那拨","score":s(("enneagram.type7",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"保持中立，两边都处","score":s(("enneagram.type9",2),("mbti.F",1),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"不参与，做好自己的事","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"试图让两边和好","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
],["harmony","includer","connectedness"],["academic-stress","relationship-conflict","self-exploration"],3,"青少年·人际"),

fc("和好朋友吵架后，我通常先","interpersonal-relationship",[
    {"text":"主动找对方和解","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"等对方先来找我","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"装作什么都没发生","score":s(("enneagram.type9",2),("mbti.P",2),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"冷静几天再谈","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
],["harmony","relator","empathy"],["academic-stress","relationship-conflict","self-exploration"],2,"青少年·人际"),

fc("对新转来的同学，我的态度","interpersonal-relationship",[
    {"text":"主动去打招呼聊天","score":s(("enneagram.type2",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"观察几天再决定","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",1),("gallup.strategic_thinking",2))},
    {"text":"等他主动来找我","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"看其他同学怎么对他","score":s(("enneagram.type6",2),("mbti.F",1),("holland.S",2),("gallup.relationship_building",1))},
],["woo","includer","individualization"],["academic-stress","self-exploration","relationship-conflict"],2,"青少年·人际"),

fc("在班级群聊里，我的角色是","interpersonal-relationship",[
    {"text":"经常发言，活跃气氛","score":s(("enneagram.type7",2),("mbti.E",2),("holland.S",2),("gallup.influencing",2))},
    {"text":"偶尔发有用信息","score":s(("enneagram.type5",2),("mbti.T",1),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"主要看别人聊","score":s(("enneagram.type9",2),("mbti.I",2),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"组织活动时才发言","score":s(("enneagram.type3",2),("mbti.J",2),("holland.E",2),("gallup.influencing",2))},
],["communication","woo","command"],["academic-stress","self-exploration"],2,"青少年·人际"),

fc("面对同伴压力让我做不想做的","interpersonal-relationship",[
    {"text":"直接拒绝，不怕得罪人","score":s(("enneagram.type8",2),("mbti.T",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"找借口委婉推掉","score":s(("enneagram.type3",2),("mbti.F",1),("holland.E",2),("gallup.influencing",1))},
    {"text":"勉强跟着做","score":s(("enneagram.type6",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",1))},
    {"text":"沉默不表态","score":s(("enneagram.type9",2),("mbti.I",2),("holland.A",1))},
],["self-assurance","command","harmony"],["academic-stress","relationship-conflict","self-exploration"],3,"青少年·人际"),

# B3. emotion-self（4题）
fc("考试考砸了，我最先想到的是","emotion-self",[
    {"text":"哪里出了问题，下次怎么改","score":s(("enneagram.type1",2),("mbti.T",2),("holland.C",2),("gallup.executing",2))},
    {"text":"对不起爸妈的付出","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"觉得自己什么都做不好","score":s(("enneagram.type4",2),("mbti.F",2),("holland.A",2))},
    {"text":"下次一定能考好","score":s(("enneagram.type3",2),("mbti.E",1),("holland.E",2),("gallup.executing",2))},
],["restorative","responsibility","self-assurance"],["academic-stress","self-exploration"],2,"青少年·情绪"),

fc("同学夸我的时候，我内心","emotion-self",[
    {"text":"开心，觉得自己不错","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"有点不好意思","score":s(("enneagram.type9",2),("mbti.I",1),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"怀疑是不是真心的","score":s(("enneagram.type6",2),("mbti.I",2),("holland.A",1),("gallup.strategic_thinking",2))},
    {"text":"觉得还不够，继续努力","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
],["significance","self-assurance","maximizer"],["academic-stress","self-exploration"],3,"青少年·情绪"),

fc("对未来感到迷茫的时候，我会","emotion-self",[
    {"text":"列计划一步步探索","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"找人聊聊缓解焦虑","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"让自己忙起来不去想","score":s(("enneagram.type7",2),("mbti.E",2),("holland.E",2),("gallup.executing",1))},
    {"text":"独处思考很久","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
],["focus","ideation","intellection"],["study-direction","self-exploration","career-choice"],3,"青少年·情绪"),

l7("我对自己外貌的满意度","emotion-self",[
    {"text":"非常满意","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"比较满意","score":s(("enneagram.type7",1),("mbti.E",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"稍微满意","score":s(("enneagram.type2",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"一般","score":s(("enneagram.type9",1),("mbti.P",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"稍微不满意","score":s(("enneagram.type1",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"比较不满意","score":s(("enneagram.type4",1),("mbti.I",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"非常不满意","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2))},
],["self-assurance","significance"],["academic-stress","self-exploration"],2,"青少年·情绪·likert-7"),

# B4. motivation-value（3题）
fc("如果有一天空闲，我最想做什么","motivation-value",[
    {"text":"约朋友出去玩","score":s(("enneagram.type7",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"在家看书或追剧","score":s(("enneagram.type5",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"运动或做手工","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"研究感兴趣的新东西","score":s(("enneagram.type7",1),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
],["adaptability","learner","activator"],["academic-stress","self-exploration","study-direction"],2,"青少年·动机·含R"),

rk("我觉得学习最核心的意义是","motivation-value",[
    {"text":"考上好学校找好工作","score":s(("enneagram.type3",2),("mbti.J",2),("holland.E",2),("gallup.executing",2))},
    {"text":"变得更聪明更有能力","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"帮助别人，回馈社会","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"探索世界发现自我","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
],["belief","learner","significance"],["study-direction","academic-stress","self-exploration"],3,"青少年·动机·ranking"),

l5("别人怎么看我，对我的影响","motivation-value",[
    {"text":"完全不在乎","score":s(("enneagram.type8",2),("mbti.T",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"不太在乎","score":s(("enneagram.type5",1),("mbti.I",1),("holland.I",1),("gallup.strategic_thinking",2))},
    {"text":"有时候会在乎","score":s(("enneagram.type3",1),("mbti.E",1),("holland.S",1),("gallup.influencing",1))},
    {"text":"比较在乎","score":s(("enneagram.type2",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"非常在乎","score":s(("enneagram.type3",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
],["significance","woo","self-assurance"],["academic-stress","self-exploration","relationship-conflict"],3,"青少年·动机·likert-5"),

# B5. action-habit（3题）
fc("放学后的时间，我通常怎么安排","action-habit",[
    {"text":"先写完作业再玩","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"先玩一会儿再写","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"边写边玩，交替进行","score":s(("enneagram.type3",1),("mbti.P",1),("holland.E",1),("gallup.executing",1))},
    {"text":"等晚饭后集中写","score":s(("enneagram.type9",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
],["discipline","focus","achiever"],["academic-stress","study-direction"],2,"青少年·行动"),

fc("我的房间通常是什么状态","action-habit",[
    {"text":"整洁有序，东西归位","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"乱但我知道东西在哪","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"偶尔整理，很快变乱","score":s(("enneagram.type3",1),("mbti.P",1),("holland.E",1),("gallup.executing",1))},
    {"text":"堆满了各种收藏品","score":s(("enneagram.type5",2),("mbti.I",1),("holland.I",2),("gallup.strategic_thinking",2))},
],["discipline","arranger","input"],["academic-stress","self-exploration"],1,"青少年·行动"),

l5("定下的目标我通常","action-habit",[
    {"text":"一定会完成","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"大部分能完成","score":s(("enneagram.type3",1),("mbti.J",1),("holland.E",1),("gallup.executing",1))},
    {"text":"完成一半左右","score":s(("enneagram.type7",1),("mbti.P",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"经常半途而废","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2))},
    {"text":"几乎没完成过","score":s(("enneagram.type9",2),("mbti.P",2),("holland.S",2))},
],["focus","achiever","discipline"],["academic-stress","study-direction","self-exploration"],2,"青少年·行动·likert-5"),

# B6. stress-response（3题）
fc("被老师当众批评后，我会","stress-response",[
    {"text":"表面没事，内心很受伤","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"反思自己哪里做错了","score":s(("enneagram.type1",2),("mbti.T",2),("holland.C",2),("gallup.executing",2))},
    {"text":"找朋友倾诉","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"不当回事，很快忘记","score":s(("enneagram.type7",2),("mbti.E",1),("holland.A",2))},
],["adaptability","empathy","positivity"],["academic-stress","self-exploration"],2,"青少年·压力"),

fc("考试前一夜，我通常","stress-response",[
    {"text":"正常作息，心态平稳","score":s(("enneagram.type9",2),("mbti.J",1),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"紧张但能睡着","score":s(("enneagram.type6",2),("mbti.F",1),("holland.S",2),("gallup.strategic_thinking",1))},
    {"text":"失眠到很晚","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"通宵复习","score":s(("enneagram.type3",2),("mbti.J",2),("holland.E",2),("gallup.executing",2))},
],["adaptability","focus","discipline"],["academic-stress"],2,"青少年·压力"),

fc("父母吵架时，我的反应是","stress-response",[
    {"text":"躲到房间里不出声","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"试图调解他们的矛盾","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"大声让他们别吵了","score":s(("enneagram.type8",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"假装没听到","score":s(("enneagram.type9",2),("mbti.P",2),("holland.A",1))},
],["harmony","adaptability","command"],["academic-stress","relationship-conflict","self-exploration"],3,"青少年·压力"),

# B7. decision-making（2题）
fc("选文理科或选科时，我主要考虑","decision-making",[
    {"text":"哪科成绩好选哪科","score":s(("enneagram.type3",2),("mbti.T",2),("holland.E",2),("gallup.executing",2))},
    {"text":"哪科更有兴趣选哪科","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"听父母和老师建议","score":s(("enneagram.type6",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"哪科对将来有用选哪科","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
],["deliberative","analytical","focus"],["study-direction","career-choice","academic-stress"],3,"青少年·决策"),

fc("面对两个都喜欢的社团，我会","decision-making",[
    {"text":"两个都参加，忙就忙点","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.executing",2))},
    {"text":"选更能锻炼能力的","score":s(("enneagram.type8",2),("mbti.T",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"选朋友多的那个","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"选更轻松有趣的","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["arranger","maximizer","adaptability"],["academic-stress","self-exploration","study-direction"],2,"青少年·决策"),

# ═══════════════════════════════════════════════════
# C. 新量表类型（25题）— likert-5(10) / likert-7(8) / ranking(7)
# ═══════════════════════════════════════════════════

# C1. likert-5（10题）
l5("面对不确定性，我的舒适程度","decision-making",[
    {"text":"非常享受不确定性","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"比较享受","score":s(("enneagram.type7",1),("mbti.P",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"一般，能接受","score":s(("enneagram.type3",1),("mbti.T",1),("holland.E",1),("gallup.executing",1))},
    {"text":"不太舒服","score":s(("enneagram.type6",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"非常不舒服","score":s(("enneagram.type6",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
],["adaptability","deliberative","strategic"],["career-choice","career-transition","self-exploration","life-transition","fresh-grad"],3,"likert-5·决策"),

l5("我在团队中发挥影响力的程度","interpersonal-relationship",[
    {"text":"非常强，经常主导","score":s(("enneagram.type8",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"比较强","score":s(("enneagram.type3",1),("mbti.E",1),("holland.E",1),("gallup.influencing",1))},
    {"text":"一般","score":s(("enneagram.type9",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"比较弱","score":s(("enneagram.type5",1),("mbti.I",1),("holland.I",1),("gallup.strategic_thinking",1))},
    {"text":"几乎没有","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["command","communication"],["leadership-growth","mid-career","entrepreneur-stage","self-exploration","fresh-grad"],3,"likert-5·人际"),

l5("我对细节的关注程度","action-habit",[
    {"text":"非常注重每个细节","score":s(("enneagram.type1",2),("mbti.S",2),("holland.C",2),("gallup.executing",2))},
    {"text":"比较注重","score":s(("enneagram.type1",1),("mbti.S",1),("holland.C",1),("gallup.executing",1))},
    {"text":"一般","score":s(("enneagram.type3",1),("mbti.T",1),("holland.E",1),("gallup.executing",1))},
    {"text":"只看大局","score":s(("enneagram.type7",1),("mbti.N",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"完全忽略细节","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
],["focus","discipline","analytical"],["mid-career","career-choice","academic-stress","leadership-growth","self-exploration"],2,"likert-5·行动"),

l5("我对尝试新事物的开放度","motivation-value",[
    {"text":"总是主动尝试","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"比较愿意尝试","score":s(("enneagram.type3",1),("mbti.E",1),("holland.E",1),("gallup.executing",1))},
    {"text":"看情况","score":s(("enneagram.type9",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"不太愿意","score":s(("enneagram.type6",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"非常抗拒改变","score":s(("enneagram.type6",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
],["activator","learner","adaptability"],["career-transition","life-transition","self-exploration","fresh-grad","entrepreneur-stage"],2,"likert-5·动机"),

l5("我处理冲突时保持冷静的程度","conflict-choice",[
    {"text":"总是非常冷静","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"大部分时候冷静","score":s(("enneagram.type1",1),("mbti.T",1),("holland.C",1),("gallup.executing",1))},
    {"text":"一般","score":s(("enneagram.type3",1),("mbti.E",1),("holland.E",1),("gallup.influencing",1))},
    {"text":"容易激动","score":s(("enneagram.type8",1),("mbti.F",1),("holland.E",1),("gallup.influencing",1))},
    {"text":"完全控制不住","score":s(("enneagram.type8",2),("mbti.F",2),("holland.E",2),("gallup.influencing",2))},
],["deliberative","self-assurance","command"],["relationship-conflict","leadership-growth","mid-career","entrepreneur-stage","self-exploration"],3,"likert-5·冲突"),

l5("独处时我感到的舒适度","emotion-self",[
    {"text":"非常享受独处","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"比较享受","score":s(("enneagram.type4",1),("mbti.I",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"无所谓","score":s(("enneagram.type9",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"有点不自在","score":s(("enneagram.type2",1),("mbti.E",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"非常难受","score":s(("enneagram.type7",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
],["intellection","adaptability","connectedness"],["self-exploration","life-transition","academic-stress","career-transition","fresh-grad"],2,"likert-5·情绪"),

l5("我设定长期目标的频率","future-vision",[
    {"text":"总是设长期目标","score":s(("enneagram.type3",2),("mbti.J",2),("holland.E",2),("gallup.executing",2))},
    {"text":"经常设","score":s(("enneagram.type1",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"偶尔设","score":s(("enneagram.type5",1),("mbti.T",1),("holland.I",1),("gallup.strategic_thinking",1))},
    {"text":"很少设","score":s(("enneagram.type7",1),("mbti.P",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"从不设长期目标","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2))},
],["futuristic","focus","strategic"],["career-choice","study-direction","self-exploration","graduate-school","entrepreneur-stage"],2,"likert-5·未来"),

l5("面对压力时我的恢复速度","stress-response",[
    {"text":"非常快，几小时就好","score":s(("enneagram.type7",2),("mbti.E",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"比较快","score":s(("enneagram.type3",1),("mbti.E",1),("holland.E",1),("gallup.executing",1))},
    {"text":"一般","score":s(("enneagram.type9",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"比较慢","score":s(("enneagram.type6",1),("mbti.I",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"非常慢，要好几天","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["adaptability","positivity","restorative"],["academic-stress","mid-career","career-transition","life-transition","self-exploration"],3,"likert-5·压力"),

l5("我对权威和规则的服从程度","decision-making",[
    {"text":"完全服从，不质疑","score":s(("enneagram.type6",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"大部分时候服从","score":s(("enneagram.type1",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"看合不合理","score":s(("enneagram.type5",1),("mbti.T",1),("holland.I",1),("gallup.strategic_thinking",2))},
    {"text":"经常质疑","score":s(("enneagram.type8",1),("mbti.T",1),("holland.E",1),("gallup.influencing",1))},
    {"text":"几乎不服从","score":s(("enneagram.type8",2),("mbti.P",2),("holland.E",2),("gallup.influencing",2))},
],["belief","command","deliberative"],["mid-career","leadership-growth","entrepreneur-stage","self-exploration","career-transition"],4,"likert-5·决策·reverse",True),

l5("我帮助他人时的内在满足感","motivation-value",[
    {"text":"非常强烈","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"比较强烈","score":s(("enneagram.type9",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"一般","score":s(("enneagram.type3",1),("mbti.T",1),("holland.E",1),("gallup.executing",1))},
    {"text":"不太强烈","score":s(("enneagram.type5",1),("mbti.T",1),("holland.I",1),("gallup.strategic_thinking",1))},
    {"text":"几乎没有","score":s(("enneagram.type8",2),("mbti.T",2),("holland.E",2),("gallup.influencing",2))},
],["developer","empathy","connectedness"],["self-exploration","relationship-conflict","leadership-growth","mid-career","fresh-grad"],3,"likert-5·动机"),

# C2. likert-7（8题）— 连续谱设计
l7("做决定时我依赖直觉的程度","decision-making",[
    {"text":"完全靠直觉","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"大部分靠直觉","score":s(("enneagram.type7",1),("mbti.N",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"偏直觉","score":s(("enneagram.type2",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"直觉和理性各半","score":s(("enneagram.type3",1),("mbti.T",1),("holland.E",1),("gallup.executing",1))},
    {"text":"偏理性","score":s(("enneagram.type1",1),("mbti.T",1),("holland.C",1),("gallup.executing",1))},
    {"text":"大部分靠理性","score":s(("enneagram.type5",1),("mbti.T",1),("holland.I",1),("gallup.strategic_thinking",1))},
    {"text":"完全靠理性分析","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
],["strategic","analytical","intellection"],["career-choice","career-transition","self-exploration","leadership-growth","fresh-grad","entrepreneur-stage"],4,"likert-7·直觉vs理性"),

l7("我在社交场合的活跃程度","interpersonal-relationship",[
    {"text":"总是成为焦点","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"经常主动社交","score":s(("enneagram.type7",1),("mbti.E",1),("holland.S",1),("gallup.relationship_building",2))},
    {"text":"比较活跃","score":s(("enneagram.type2",1),("mbti.E",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"看场合","score":s(("enneagram.type9",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"偏安静","score":s(("enneagram.type5",1),("mbti.I",1),("holland.I",1),("gallup.strategic_thinking",1))},
    {"text":"大部分时候沉默","score":s(("enneagram.type4",1),("mbti.I",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"几乎不说话","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
],["woo","communication","relator"],["self-exploration","fresh-grad","mid-career","entrepreneur-stage","academic-stress","relationship-conflict"],2,"likert-7·社交活跃度"),

l7("我对规则和结构的偏好程度","action-habit",[
    {"text":"完全按规则来","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"大部分时候按规则","score":s(("enneagram.type1",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"偏规则","score":s(("enneagram.type6",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"规则和灵活各半","score":s(("enneagram.type3",1),("mbti.T",1),("holland.E",1),("gallup.executing",1))},
    {"text":"偏灵活","score":s(("enneagram.type7",1),("mbti.P",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"大部分时候灵活","score":s(("enneagram.type7",1),("mbti.P",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"完全即兴发挥","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",2))},
],["discipline","adaptability","arranger"],["mid-career","academic-stress","career-choice","entrepreneur-stage","leadership-growth","self-exploration"],3,"likert-7·规则vs灵活"),

l7("我对风险和安全的偏好","motivation-value",[
    {"text":"极度追求风险","score":s(("enneagram.type8",2),("mbti.P",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"很喜欢风险","score":s(("enneagram.type7",1),("mbti.P",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"偏冒险","score":s(("enneagram.type3",1),("mbti.E",1),("holland.E",1),("gallup.executing",1))},
    {"text":"中性","score":s(("enneagram.type5",1),("mbti.T",1),("holland.I",1),("gallup.strategic_thinking",1))},
    {"text":"偏保守","score":s(("enneagram.type6",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"很保守","score":s(("enneagram.type6",1),("mbti.J",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"极度回避风险","score":s(("enneagram.type6",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
],["self-assurance","deliberative","belief"],["career-choice","career-transition","entrepreneur-stage","self-exploration","life-transition","fresh-grad"],3,"likert-7·风险偏好"),

l7("我关注当下vs未来的程度","future-vision",[
    {"text":"完全活在当下","score":s(("enneagram.type7",2),("mbti.S",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"大部分关注当下","score":s(("enneagram.type7",1),("mbti.S",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"偏当下","score":s(("enneagram.type9",1),("mbti.S",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"当下和未来各半","score":s(("enneagram.type3",1),("mbti.T",1),("holland.E",1),("gallup.executing",1))},
    {"text":"偏未来","score":s(("enneagram.type5",1),("mbti.N",1),("holland.I",1),("gallup.strategic_thinking",1))},
    {"text":"大部分关注未来","score":s(("enneagram.type1",1),("mbti.N",1),("holland.C",1),("gallup.executing",1))},
    {"text":"完全沉浸在未来愿景","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
],["futuristic","adaptability","focus"],["career-choice","study-direction","self-exploration","entrepreneur-stage","graduate-school","life-transition"],4,"likert-7·当下vs未来"),

l7("我的情绪波动幅度","emotion-self",[
    {"text":"极其稳定","score":s(("enneagram.type9",2),("mbti.T",2),("holland.C",2),("gallup.executing",2))},
    {"text":"很稳定","score":s(("enneagram.type5",1),("mbti.T",1),("holland.I",1),("gallup.strategic_thinking",1))},
    {"text":"偏稳定","score":s(("enneagram.type1",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"中等","score":s(("enneagram.type3",1),("mbti.T",1),("holland.E",1),("gallup.executing",1))},
    {"text":"偏波动","score":s(("enneagram.type2",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"很波动","score":s(("enneagram.type4",1),("mbti.F",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"极其波动","score":s(("enneagram.type4",2),("mbti.F",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["adaptability","self-assurance","empathy"],["self-exploration","academic-stress","relationship-conflict","mid-career","career-transition","life-transition"],3,"likert-7·情绪稳定性"),

l7("我追求完美vs完成优先","action-habit",[
    {"text":"追求极致完美","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"很注重完美","score":s(("enneagram.type1",1),("mbti.J",1),("holland.C",1),("gallup.executing",1))},
    {"text":"偏完美","score":s(("enneagram.type4",1),("mbti.N",1),("holland.A",1),("gallup.strategic_thinking",1))},
    {"text":"平衡","score":s(("enneagram.type3",1),("mbti.T",1),("holland.E",1),("gallup.executing",1))},
    {"text":"偏完成","score":s(("enneagram.type3",1),("mbti.E",1),("holland.E",1),("gallup.executing",1))},
    {"text":"很注重效率","score":s(("enneagram.type8",1),("mbti.T",1),("holland.E",1),("gallup.influencing",1))},
    {"text":"完成就好不管质量","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2))},
],["maximizer","achiever","activator"],["mid-career","academic-stress","career-choice","entrepreneur-stage","leadership-growth","fresh-grad"],3,"likert-7·完美vs效率"),

l7("我对竞争的态度","conflict-choice",[
    {"text":"极度享受竞争","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"很喜欢竞争","score":s(("enneagram.type8",1),("mbti.T",1),("holland.E",1),("gallup.influencing",1))},
    {"text":"偏竞争","score":s(("enneagram.type3",1),("mbti.E",1),("holland.E",1),("gallup.executing",1))},
    {"text":"中性","score":s(("enneagram.type5",1),("mbti.T",1),("holland.I",1),("gallup.strategic_thinking",1))},
    {"text":"偏合作","score":s(("enneagram.type9",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"很喜欢合作","score":s(("enneagram.type2",1),("mbti.F",1),("holland.S",1),("gallup.relationship_building",1))},
    {"text":"极度偏好合作","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
],["competition","harmony","command"],["mid-career","leadership-growth","entrepreneur-stage","academic-stress","career-choice","fresh-grad"],3,"likert-7·竞争vs合作"),

# C3. ranking（7题）
rk("选择工作时，我最看重的因素","work-career",[
    {"text":"薪资待遇和福利","score":s(("enneagram.type3",2),("mbti.S",2),("holland.E",2),("gallup.executing",2))},
    {"text":"工作内容和兴趣匹配","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"团队氛围和人际关系","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"成长空间和学习机会","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
],["significance","learner","relator"],["career-choice","fresh-grad","career-transition","mid-career","graduate-school"],3,"ranking·工作选择"),

rk("我生活中最重要的方面","motivation-value",[
    {"text":"事业成就","score":s(("enneagram.type3",2),("mbti.J",2),("holland.E",2),("gallup.executing",2))},
    {"text":"家庭关系","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"个人成长","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"自由体验","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["belief","responsibility","significance"],["self-exploration","career-choice","life-transition","mid-career","fresh-grad"],4,"ranking·生活价值观"),

rk("面对困难时，我最依赖的资源","stress-response",[
    {"text":"自己的分析和判断","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"家人朋友的支持","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"过往的经验","score":s(("enneagram.type6",2),("mbti.S",2),("holland.C",2),("gallup.executing",2))},
    {"text":"直觉和灵感","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
],["restorative","connectedness","input"],["academic-stress","career-transition","life-transition","mid-career","self-exploration"],3,"ranking·应对资源"),

rk("我希望被别人记住的特质","future-vision",[
    {"text":"专业能力和成就","score":s(("enneagram.type3",2),("mbti.T",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"善良和温暖","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"智慧和洞察","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"创造力和独特性","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
],["significance","connectedness"],["self-exploration","life-transition","leadership-growth","mid-career","fresh-grad"],4,"ranking·个人遗产"),

rk("学习新技能时，我最看重的","learning-cognition",[
    {"text":"理论体系完整","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"能马上用起来","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"有人一起学","score":s(("enneagram.type2",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"有创新空间","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
],["learner","input","ideation"],["study-direction","career-choice","academic-stress","graduate-school","self-exploration"],3,"ranking·学习偏好·含R"),

rk("在亲密关系中，我最需要的","interpersonal-relationship",[
    {"text":"信任和忠诚","score":s(("enneagram.type6",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"激情和浪漫","score":s(("enneagram.type7",2),("mbti.E",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"理解和支持","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"独立和空间","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
],["relator","empathy","individualization"],["relationship-conflict","self-exploration","life-transition","fresh-grad","mid-career"],4,"ranking·亲密关系需求"),

rk("面对冲突时，我最看重的","conflict-choice",[
    {"text":"维护自己的立场","score":s(("enneagram.type8",2),("mbti.T",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"维护关系和谐","score":s(("enneagram.type9",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"找到最优方案","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"快速翻篇不再纠结","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["command","harmony","restorative"],["relationship-conflict","leadership-growth","mid-career","self-exploration","entrepreneur-stage"],3,"ranking·冲突处理"),

# ═══════════════════════════════════════════════════
# D. 四体系多维度强化（40题）— 重点补holland覆盖
# ═══════════════════════════════════════════════════

# D1. 补holland R型（10题）
fc("周末如果有空地和时间，我想","action-habit",[
    {"text":"种菜种花打理花园","score":s(("enneagram.type9",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"做木工或修东西","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"画画或写东西","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"研究投资或看书","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
],["achiever","restorative","learner"],["self-exploration","mid-career","life-transition","career-transition","parenting-teen"],2,"R型·含动手场景"),

fc("面对家里的维修需求，我","action-habit",[
    {"text":"自己动手修好","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"看视频学着修","score":s(("enneagram.type5",2),("mbti.N",1),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"花钱请人来修","score":s(("enneagram.type3",2),("mbti.T",1),("holland.E",2),("gallup.executing",1))},
    {"text":"先放着等必须修再说","score":s(("enneagram.type9",2),("mbti.P",2),("holland.S",1))},
],["restorative","achiever","focus"],["self-exploration","mid-career","life-transition","parenting-teen","career-transition"],2,"R型·含动手场景"),

fc("如果学一门新手艺，我会选","motivation-value",[
    {"text":"烹饪或烘焙","score":s(("enneagram.type2",2),("mbti.S",2),("holland.R",2),("gallup.relationship_building",2))},
    {"text":"编程或数据分析","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"摄影或设计","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"演讲或销售","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
],["learner","input","achiever"],["self-exploration","career-transition","life-transition","fresh-grad","mid-career"],2,"R型·含烹饪场景"),

fc("户外活动时我最享受的是","motivation-value",[
    {"text":"徒步登山挑战体能","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"观察自然拍照片","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"和朋友一起露营聊天","score":s(("enneagram.type2",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"研究动植物分类","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
],["achiever","learner","connectedness"],["self-exploration","life-transition","academic-stress","career-transition","mid-career"],2,"R型·含户外场景"),

fc("逛超市时我最喜欢看的区域","motivation-value",[
    {"text":"五金工具区","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"书籍文具区","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"生鲜食材区","score":s(("enneagram.type2",2),("mbti.S",1),("holland.R",1),("gallup.relationship_building",2))},
    {"text":"家居装饰区","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["input","learner","maximizer"],["self-exploration","life-transition","mid-career","parenting-teen","career-transition"],2,"R型·含日常场景"),

fc("旅行时我最想体验的项目","future-vision",[
    {"text":"攀岩漂流等极限运动","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"博物馆和历史遗迹","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"当地集市和民俗体验","score":s(("enneagram.type2",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"艺术展和音乐节","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["activator","learner","woo"],["self-exploration","life-transition","fresh-grad","career-transition","study-abroad"],2,"R型·含极限场景"),

fc("组装家具或拼装模型时，我","action-habit",[
    {"text":"不看说明直接上手","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"仔细看说明再动手","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"边看说明边做","score":s(("enneagram.type3",1),("mbti.T",1),("holland.E",1),("gallup.executing",1))},
    {"text":"让别人帮我装","score":s(("enneagram.type7",2),("mbti.P",2),("holland.S",1),("gallup.relationship_building",1))},
],["restorative","focus","achiever"],["self-exploration","academic-stress","life-transition","mid-career","fresh-grad"],2,"R型·含组装场景"),

fc("如果做志愿者，我会选择","motivation-value",[
    {"text":"去工地盖房子修路","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"教孩子读书","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"做科研数据收集","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"组织活动策划","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
],["belief","developer","responsibility"],["self-exploration","life-transition","fresh-grad","career-transition","academic-stress"],3,"R型·含体力志愿"),

fc("我更喜欢哪种运动方式","action-habit",[
    {"text":"打球或跑步等竞技运动","score":s(("enneagram.type3",2),("mbti.E",2),("holland.R",2),("gallup.influencing",2))},
    {"text":"瑜伽或太极等内修运动","score":s(("enneagram.type9",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"游泳或骑行等单人运动","score":s(("enneagram.type5",2),("mbti.I",1),("holland.R",1),("gallup.strategic_thinking",2))},
    {"text":"跳舞或表演等艺术运动","score":s(("enneagram.type7",2),("mbti.E",2),("holland.A",2),("gallup.influencing",1))},
],["competition","achiever","adaptability"],["self-exploration","academic-stress","mid-career","life-transition","career-transition"],2,"R型·含竞技运动"),

fc("选择居住环境时，我最想要","future-vision",[
    {"text":"带院子能种东西的房子","score":s(("enneagram.type9",2),("mbti.S",2),("holland.R",2),("gallup.executing",1))},
    {"text":"市中心交通方便的公寓","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.executing",2))},
    {"text":"文化氛围浓的社区","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"学区好的安静小区","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
],["adaptability","belief","connectedness"],["self-exploration","life-transition","parenting-teen","career-transition","mid-career"],3,"R型·含院子种植"),

# D2. 补holland各型不足的类别（15题）
fc("我做事最大的动力来源是","motivation-value",[
    {"text":"实现目标和获得认可","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"探索未知和获取知识","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"帮助他人和建立连接","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"创造美好和表达自我","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["significance","learner","developer"],["self-exploration","career-choice","mid-career","fresh-grad","life-transition"],3,"holland补强·动机"),

fc("如果有一笔启动资金，我会","motivation-value",[
    {"text":"开一家有特色的店","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"投资研发一个新技术","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"做公益帮助需要的人","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"开个工作室做手作","score":s(("enneagram.type4",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
],["activator","belief","maximizer"],["entrepreneur-stage","career-transition","self-exploration","life-transition","fresh-grad"],4,"holland补强·动机·含R"),

fc("我觉得最有价值的工作是能","motivation-value",[
    {"text":"直接影响商业结果","score":s(("enneagram.type3",2),("mbti.T",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"推动科技进步","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"改善他人生活","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"创造美的体验","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["significance","belief","developer"],["career-choice","mid-career","fresh-grad","self-exploration","entrepreneur-stage"],3,"holland补强·动机"),

fc("面对别人的情绪爆发，我","emotion-self",[
    {"text":"理性分析他为什么这样","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"感同身受地安慰","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"直接告诉他冷静下来","score":s(("enneagram.type8",2),("mbti.T",1),("holland.E",2),("gallup.influencing",2))},
    {"text":"被影响也变得情绪化","score":s(("enneagram.type4",2),("mbti.F",2),("holland.A",2))},
],["empathy","harmony","command"],["relationship-conflict","self-exploration","mid-career","leadership-growth","fresh-grad"],3,"holland补强·情绪"),

fc("我觉得最舒服的表达方式","emotion-self",[
    {"text":"写文章或日记","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"当面口头表达","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"做东西或动手展示","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"通过帮助他人来表达","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
],["communication","ideation","self-assurance"],["self-exploration","relationship-conflict","academic-stress","mid-career","fresh-grad"],2,"holland补强·情绪·含R"),

fc("在团队中我通常负责","work-career",[
    {"text":"制定流程和规范","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"攻关技术难题","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"维护团队氛围","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"推动项目落地","score":s(("enneagram.type8",2),("mbti.E",2),("holland.E",2),("gallup.executing",2))},
],["arranger","responsibility","command"],["mid-career","leadership-growth","entrepreneur-stage","fresh-grad","career-transition"],3,"holland补强·工作"),

fc("我处理信息时更依赖","learning-cognition",[
    {"text":"数据和事实","score":s(("enneagram.type5",2),("mbti.S",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"直觉和灵感","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"他人的反馈","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"实操验证","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
],["analytical","input","intellection"],["study-direction","career-choice","academic-stress","mid-career","self-exploration"],3,"holland补强·学习·含R"),

fc("面对新环境，我的适应策略","stress-response",[
    {"text":"观察规律再行动","score":s(("enneagram.type5",2),("mbti.I",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"主动社交快速融入","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"找老乡或同好抱团","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"按自己的节奏慢慢来","score":s(("enneagram.type9",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["adaptability","woo","connectedness"],["fresh-grad","career-transition","study-abroad","life-transition","academic-stress"],3,"holland补强·压力"),

fc("我觉得最有意义的成就是","future-vision",[
    {"text":"创办一家成功的企业","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"发表有影响力的研究","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"帮助很多人改变命运","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"创作打动人心的作品","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
],["significance","futuristic","belief"],["self-exploration","career-choice","entrepreneur-stage","mid-career","fresh-grad"],4,"holland补强·未来"),

fc("面对两难选择，我的判断依据","decision-making",[
    {"text":"哪个更符合逻辑","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"哪个对大家好","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"哪个收益最大","score":s(("enneagram.type3",2),("mbti.T",1),("holland.E",2),("gallup.executing",2))},
    {"text":"哪个更有创意","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
],["deliberative","analytical","belief"],["career-choice","career-transition","life-transition","mid-career","fresh-grad"],3,"holland补强·决策"),

fc("工作中我最享受的环节","work-career",[
    {"text":"从零搭建一个系统","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"分析数据找规律","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"和客户沟通需求","score":s(("enneagram.type2",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"策划创意方案","score":s(("enneagram.type7",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["achiever","analytical","communication"],["mid-career","career-choice","fresh-grad","entrepreneur-stage","career-transition"],2,"holland补强·工作·含R"),

fc("遇到人际矛盾，我的第一反应","conflict-choice",[
    {"text":"分析谁对谁错","score":s(("enneagram.type1",2),("mbti.T",2),("holland.C",2),("gallup.executing",2))},
    {"text":"先安抚双方情绪","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"用自己的方式解决","score":s(("enneagram.type8",2),("mbti.T",1),("holland.E",2),("gallup.influencing",2))},
    {"text":"随它去吧","score":s(("enneagram.type9",2),("mbti.P",2),("holland.A",1))},
],["harmony","restorative","command"],["relationship-conflict","mid-career","leadership-growth","self-exploration","fresh-grad"],2,"holland补强·冲突"),

fc("我的学习风格更偏向","learning-cognition",[
    {"text":"系统理论先行","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"做中学边练边悟","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"讨论碰撞中学习","score":s(("enneagram.type7",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"按部就班跟教程","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
],["learner","input","ideation"],["study-direction","career-choice","academic-stress","graduate-school","fresh-grad"],2,"holland补强·学习·含R"),

# D3. 跨年龄段通用题（15题）— 覆盖全年龄段的通用场景
fc("面对一个复杂问题，我倾向","decision-making",[
    {"text":"拆解成小步骤逐一解决","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"找底层规律一击破之","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"找有经验的人帮忙","score":s(("enneagram.type6",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"先试试看再说","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["analytical","strategic","restorative"],["self-exploration","career-choice","academic-stress","mid-career","life-transition"],3,"跨年龄·决策"),

fc("我对时间管理的态度","action-habit",[
    {"text":"精确到分钟安排","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"有大致计划但灵活","score":s(("enneagram.type3",1),("mbti.J",1),("holland.E",1),("gallup.executing",1))},
    {"text":"看心情随意安排","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"跟着ddl走","score":s(("enneagram.type9",1),("mbti.P",1),("holland.S",1),("gallup.relationship_building",1))},
],["discipline","focus","arranger"],["academic-stress","mid-career","career-choice","fresh-grad","self-exploration"],2,"跨年龄·行动"),

fc("面对批评，我内心的反应","emotion-self",[
    {"text":"虚心接受，立即改进","score":s(("enneagram.type1",2),("mbti.T",2),("holland.C",2),("gallup.executing",2))},
    {"text":"先处理情绪再处理事","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"据理力争，维护自己","score":s(("enneagram.type8",2),("mbti.T",1),("holland.E",2),("gallup.influencing",2))},
    {"text":"表面接受，内心不服","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",1))},
],["restorative","self-assurance","adaptability"],["mid-career","academic-stress","leadership-growth","self-exploration","fresh-grad"],3,"跨年龄·情绪"),

fc("我对成功的定义","motivation-value",[
    {"text":"社会地位和经济实力","score":s(("enneagram.type3",2),("mbti.J",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"内心平静和自我接纳","score":s(("enneagram.type9",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"在领域内有深度贡献","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"活出独特的人生","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
],["significance","belief","futuristic"],["self-exploration","career-choice","mid-career","fresh-grad","life-transition"],4,"跨年龄·动机"),

fc("遇到完全陌生的领域，我","learning-cognition",[
    {"text":"先看书系统学理论","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"直接上手试错","score":s(("enneagram.type8",2),("mbti.S",2),("holland.R",2),("gallup.executing",2))},
    {"text":"报班跟老师学","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"找人带我入门","score":s(("enneagram.type2",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
],["learner","input","activator"],["career-choice","career-transition","self-exploration","fresh-grad","study-direction"],3,"跨年龄·学习·含R"),

fc("长期高压下我的身体信号","stress-response",[
    {"text":"失眠或睡眠质量下降","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"肩颈疼痛或头痛","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"肠胃不适或食欲变化","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"容易疲劳精力不济","score":s(("enneagram.type9",2),("mbti.P",2),("holland.S",1),("gallup.relationship_building",1))},
],["restorative","adaptability","deliberative"],["academic-stress","mid-career","career-transition","life-transition","parenting-teen"],3,"跨年龄·压力"),

fc("和不同年龄的人交流时，我","interpersonal-relationship",[
    {"text":"能自然找到共同话题","score":s(("enneagram.type7",2),("mbti.E",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"更愿意和同龄人交流","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"向年长者请教经验","score":s(("enneagram.type6",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"用专业知识拉平差距","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
],["woo","relator","individualization"],["self-exploration","mid-career","fresh-grad","leadership-growth","parenting-teen"],3,"跨年龄·人际"),

fc("如果可以重新选择专业方向","future-vision",[
    {"text":"选更实用的工科商科","score":s(("enneagram.type3",2),("mbti.S",2),("holland.E",2),("gallup.executing",2))},
    {"text":"选更有深度的理科","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"选更有温度的人文社科","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"选更有创意的艺术设计","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))},
],["futuristic","belief","maximizer"],["career-choice","career-transition","self-exploration","fresh-grad","life-transition"],3,"跨年龄·未来"),

fc("面对规则不合理的情况，我","conflict-choice",[
    {"text":"按规则来，同时提建议","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"直接挑战不合理之处","score":s(("enneagram.type8",2),("mbti.T",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"想办法绕过去","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"忍了，不值得对抗","score":s(("enneagram.type9",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
],["belief","command","harmony"],["mid-career","academic-stress","leadership-growth","entrepreneur-stage","self-exploration"],3,"跨年龄·冲突"),

fc("我对物质生活的态度","motivation-value",[
    {"text":"够用就行，不追求","score":s(("enneagram.type9",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"适度享受，量力而行","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"追求品质，愿意投入","score":s(("enneagram.type3",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"极简主义，越少越好","score":s(("enneagram.type4",2),("mbti.N",2),("holland.A",2),("gallup.strategic_thinking",2))}
],["belief","significance","maximizer"],["self-exploration","mid-career","career-choice","life-transition","fresh-grad"],3,"跨年龄·动机"),

fc("我觉得最好的领导风格","work-career",[
    {"text":"以身作则，带头干","score":s(("enneagram.type8",2),("mbti.E",2),("holland.E",2),("gallup.influencing",2))},
    {"text":"放权信任，给空间","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"关心下属，亦师亦友","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"建立流程，规范运作","score":s(("enneagram.type1",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))}
],["command","developer","harmony"],["leadership-growth","mid-career","entrepreneur-stage","self-exploration","career-transition"],3,"跨年龄·工作"),

fc("我对改变的习惯","action-habit",[
    {"text":"主动寻求改变","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",2))},
    {"text":"需要理由才会改变","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"被推动才改变","score":s(("enneagram.type6",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"尽量不变","score":s(("enneagram.type9",2),("mbti.I",2),("holland.S",2),("gallup.relationship_building",2))}
],["adaptability","activator","belief"],["self-exploration","life-transition","career-transition","mid-career","fresh-grad"],3,"跨年龄·行动"),

fc("面对别人的请求帮助，我","interpersonal-relationship",[
    {"text":"二话不说就帮","score":s(("enneagram.type2",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))},
    {"text":"先评估自己能不能帮","score":s(("enneagram.type5",2),("mbti.T",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"看关系好不好","score":s(("enneagram.type3",2),("mbti.T",1),("holland.E",2),("gallup.influencing",2))},
    {"text":"能推就推","score":s(("enneagram.type4",2),("mbti.I",2),("holland.A",2),("gallup.strategic_thinking",1))}
],["developer","empathy","responsibility"],["self-exploration","relationship-conflict","mid-career","fresh-grad","academic-stress"],2,"跨年龄·人际"),

fc("我对未来的规划程度","future-vision",[
    {"text":"五年十年的清晰规划","score":s(("enneagram.type3",2),("mbti.J",2),("holland.C",2),("gallup.executing",2))},
    {"text":"有大方向但不细化","score":s(("enneagram.type5",2),("mbti.N",2),("holland.I",2),("gallup.strategic_thinking",2))},
    {"text":"走一步看一步","score":s(("enneagram.type7",2),("mbti.P",2),("holland.A",2),("gallup.strategic_thinking",1))},
    {"text":"顺其自然就好","score":s(("enneagram.type9",2),("mbti.F",2),("holland.S",2),("gallup.relationship_building",2))}
],["futuristic","focus","strategic"],["career-choice","study-direction","self-exploration","mid-career","life-transition"],3,"跨年龄·未来"),
]
