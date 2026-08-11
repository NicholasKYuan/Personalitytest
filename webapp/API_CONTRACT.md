# API 契约文档

## 基础信息
- 后端框架：FastAPI（Python 3.10+）
- 前端：纯 HTML/CSS/JS（无框架）
- 题库路径：`../question-bank/items.jsonl`
- 筛选器路径：`../selector/selector.py`

## 接口定义

### 1. 创建会话 + 获取题目

```
POST /api/session
Content-Type: application/json

请求体:
{
  "name": "小明",           // 可选，用于称呼
  "age": 22,                // 必填
  "gender": "male",         // 可选
  "role": "student-undergrad",  // 必填
  "purpose": "career-planning",  // 必填
  "current_state": "transition", // 可选
  "decision_horizon": "within-1-year", // 可选
  "birth_date": "2003-05-15"   // 可选，用于八字解读
}

响应体:
{
  "session_id": "uuid-string",
  "questions": [
    {
      "id": "Q0001",
      "stem": "聚会中认识新朋友，我更倾向于",
      "scale": "forced-choice",
      "options": [
        {"text": "主动找话题，让场面热闹起来"},
        {"text": "观察一会儿，等合适时机再加入"},
        ...
      ],
      "category": "interpersonal-relationship",
      "difficulty": 2
    },
    ...  // 共100题
  ]
}
```

### 2. 提交答案 + 获取免费结果

```
POST /api/submit
Content-Type: application/json

请求体:
{
  "session_id": "uuid-string",
  "answers": [
    {"question_id": "Q0001", "option_index": 0},
    {"question_id": "Q0002", "option_index": 2},
    ...
  ]
}

响应体:
{
  "session_id": "uuid-string",
  "results": {
    "enneagram": {
      "main_type": 3,
      "type_name": "成就者",
      "scores": {"type1": 12, "type2": 8, ...}
    },
    "mbti": {
      "type": "ENTJ",
      "dimensions": {"E": 15, "I": 5, "S": 8, "N": 12, "T": 18, "F": 2, "J": 14, "P": 6}
    },
    "holland": {
      "code": "EAS",
      "scores": {"R": 5, "I": 8, "A": 12, "S": 10, "E": 15, "C": 7}
    },
    "gallup": {
      "top_domain": "executing",
      "domains": {"executing": 20, "influencing": 12, "relationship_building": 8, "strategic_thinking": 15},
      "top_themes": ["achiever", "arranger", "focus"]
    }
  },
  "free_summary": "你的MBTI类型为ENTJ...",
  "detailed_available": true
}
```

### 3. 获取深度分析（付费）

```
POST /api/analyze
Content-Type: application/json

请求体:
{
  "session_id": "uuid-string"
}

响应体:
{
  "session_id": "uuid-string",
  "detailed_analysis": "## 九型人格深度解读\n\n...",
  "sections": [
    {"title": "九型人格深度解读", "content": "..."},
    {"title": "MBTI深度分析", "content": "..."},
    {"title": "霍兰德职业方向", "content": "..."},
    {"title": "盖洛普优势发挥", "content": "..."},
    {"title": "四体系综合交叉解读", "content": "..."},
    {"title": "盲派八字参考（如提供生日）", "content": "..."}
  ]
}
```

## 评分逻辑

每题用户选择一个选项（option_index 0-3），从题库 JSONL 中查找该题该选项的 score 字段，累加到各维度总分：

- 九型：取 type1-9 中总分最高者为主型
- MBTI：E/I 对取高者，S/N 对取高者，T/F 对取高者，J/P 对取高者，组合成4字母类型
- 霍兰德：取 R/I/A/S/E/C 中分值最高的3个组成代码
- 盖洛普：4领域分值排序，取频次最高的 top 3-5 主题

## 前端流程

1. **填写信息页**：表单收集 name/age/gender/role/purpose/current_state/birth_date
2. **答题页**：逐题或分页展示100题，用户点选选项，进度条显示
3. **结果页**：
   - 免费区：四体系类型结果 + 简要说明
   - 付费区：解锁深度分析（点击按钮 → 调 /api/analyze → 展示AI解读）
