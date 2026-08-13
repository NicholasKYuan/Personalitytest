---
name: personality-interpretation
version: 1.0.0
summary: 接收四体系评分结果与用户 profile，调用 AI 生成深度解读报告章节
description: |
  星耀启程人格测评的结果解读 skill。输入评分结果（九型人格 / MBTI / 霍兰德 / 盖洛普）
  和用户 profile，调用 Minimax M3 生成 6 章节深度解读，输出结构化章节列表供报告生成器使用。

  本 skill 可独立调用，不依赖筛选 skill 或报告生成 skill。

  触发词：解读结果、生成解读、AI 分析、深度报告、结果解读、interpretation。
---

# 结果解读 Skill

## 定位

接收四体系评分结果 + 用户 profile → 调用 AI → 输出结构化解读章节。

## 输入

```json
{
  "results": {
    "enneagram": {"main_type": 3, "type_name": "成就者", "scores": {"type1": x, ...}, "normalized": {...}},
    "mbti": {"type": "ENTJ", "dimensions": {"E": x, ...}, "normalized": {...}},
    "holland": {"code": "EAS", "scores": {"R": x, ...}, "normalized": {...}},
    "gallup": {"top_domain": "executing", "domains": {...}, "top_themes": [...], "normalized": {...}}
  },
  "profile": {
    "name": "张三",
    "age": 25,
    "gender": "male",
    "role": "employed",
    "purpose": "career-planning",
    "current_state": "transition",
    "birth_date": "2000-01-15"  // 可选，存在时触发易学结合解读
  }
}
```

## 输出

```json
{
  "detailed_analysis": "完整 markdown 文本",
  "sections": [
    {"title": "九型人格深度解读", "content": "## markdown 内容..."},
    {"title": "MBTI深度分析", "content": "## markdown 内容..."},
    {"title": "霍兰德职业方向", "content": "## markdown 内容..."},
    {"title": "盖洛普优势发挥", "content": "## markdown 内容..."},
    {"title": "四体系综合交叉解读", "content": "## markdown 内容（含 ### 协同点 / ### 张力点 / ### 融合洞察 子标题）..."},
    {"title": "传统易学结合解读", "content": "## markdown 内容（含 ### 当前发展阶段定位 / ### 近三年专注方向 / ### 阶段性格避坑提醒 / ### 与四体系交叉验证 子标题）..."}  // 仅当 birth_date 存在
  ]
}
```

## AI 章节结构

### 1. 九型人格深度解读
解读主型的核心特质、动机、恐惧、成长方向。结合用户角色和目的给出个性化洞察。

### 2. MBTI 深度分析
分析类型的认知功能、思维模式、与他人的互动风格。

### 3. 霍兰德职业方向
基于代码推荐适合的职业方向和发展路径。

### 4. 盖洛普优势发挥
解读主导领域和核心主题（中文），给出优势发挥和补盲建议。

### 5. 四体系综合交叉解读
**必须包含以下三个 `###` 子标题**：
- `### 协同点` — 列出 2-3 个四体系之间的协同亮点
- `### 张力点` — 列出 1-2 个四体系之间的张力或潜在冲突
- `### 融合洞察` — 综合四体系的整体洞察

### 6. 传统易学结合解读（仅当 birth_date 存在）
**必须包含以下四个 `###` 子标题**，每个 80-150 字：
- `### 当前发展阶段定位`
- `### 近三年专注方向`
- `### 阶段性格避坑提醒`
- `### 与四体系交叉验证`

## 关键约束

1. **禁用词过滤**：自动替换"八字"→"生命格局"、"五行"→"生命元素"等。完整映射见 `webapp/backend/ai_analyzer.py` 的 `_filter_forbidden_words()`。
2. **英文过滤**：移除 AI 推理过程文本（"Here is..."、"I'll..."等），保留中英文混排内容。
3. **盖洛普主题中文化**：传入 prompt 前将英文主题名转为中文（如 "achiever" → "成就"）。
4. **总字数**：2000-3500 字。
5. **写作风格**：禁止先列 outline 再展开，直接以完整段落进入深度解读。
6. **降级处理**：API 不可用时返回错误章节；`AI_MOCK=1` 时返回固定 mock 数据。

## 调用方式

### 方式一：Python 直接调用

```python
import sys
sys.path.insert(0, "webapp/backend")
from ai_analyzer import generate_detailed_analysis

result = generate_detailed_analysis(results, profile)
# result["sections"] 即结构化章节列表
```

### 方式二：环境变量配置

```bash
export MINIMAX_API_KEY="your-api-key"
export MINIMAX_BASE_URL="https://api.minimaxi.com/v1"
export MINIMAX_MODEL="MiniMax-M3"
export AI_MOCK=0  # 设为 1 使用 mock 数据
```

## 依赖文件

| 文件 | 用途 |
|------|------|
| `webapp/backend/ai_analyzer.py` | 核心逻辑：prompt 构建、API 调用、过滤、章节拆分 |
| `webapp/backend/scorer.py` | 评分引擎（提供 results 输入） |

## 与其他 skill 的关系

- **上游**：`skill/SKILL.md`（筛选 skill）→ 输出 120 题测评卷 → 用户作答 → `scorer.py` 计分 → 传入本 skill
- **下游**：本 skill 输出 sections → `skill/report-generator/SKILL.md`（报告生成 skill）→ 填充 HTML 模板
