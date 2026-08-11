---
name: personality-report-generator
summary: 根据四体系测评结果，生成免费简版报告或付费深度解读报告（图文兼并 HTML）
description: |
  星耀启程人格测评的报告生成 skill。输入四体系评分结果 + 用户 profile，
  输出两种 HTML 报告：免费简版（结果卡片+得分条形图+简评）或付费深度版（雷达图+柱状图+AI 深度解读+生涯发展时机建议）。
  触发词：生成报告、测评报告、深度解读、结果报告。
read_when:
  - 用户完成测评答题，需要生成结果报告
  - 需要将评分结果渲染为可视化 HTML 报告
  - 需要调用 AI 生成付费深度解读内容
---

# personality-report-generator

## 用途

将测评系统的四体系评分结果（九型/MBTI/霍兰德/盖洛普）渲染为可视化 HTML 报告。
支持两种模式：
- **simple**：免费简版 — 结果卡片 + 得分条形图 + 简要文字解读
- **detailed**：付费深度版 — 雷达图 + 柱状图 + AI 逐体系深度解读 + 交叉分析 + 可选生涯发展时机建议（基于出生日期的辅助视角）

## 文件位置

- 简单模板：`webapp/templates/result-simple.html`
- 详细模板：`webapp/templates/report-detailed.html`
- 评分器：`webapp/backend/scorer.py`（产出 results dict）
- AI 分析器：`webapp/backend/ai_analyzer.py`（产出 AI 解读文本）

## 模板占位符规范

### 通用占位符（两个模板共用）

| 占位符 | 来源 | 示例 |
|--------|------|------|
| `{{USER_NAME}}` | profile.name，缺省用"你" | 小明 |
| `{{USER_AGE}}` | profile.age | 22 |
| `{{USER_ROLE_CN}}` | profile.role → 中文映射 | 本科生 |
| `{{USER_PURPOSE_CN}}` | profile.purpose → 中文映射 | 职业规划 |
| `{{REPORT_DATE}}` | 当前日期 YYYY-MM-DD | 2026-08-11 |

### 九型人格占位符

| 占位符 | 来源 | 说明 |
|--------|------|------|
| `{{ENNEAGRAM_TYPE}}` | results.enneagram.main_type | 1-9 |
| `{{ENNEAGRAM_NAME}}` | ENNEAGRAM_NAMES[type] | 如"成就者" |
| `{{ENNEAGRAM_SCORE_1}}` ... `{{ENNEAGRAM_SCORE_9}}` | results.enneagram.scores | 各类型原始分 |
| `{{ENNEAGRAM_PCT_1}}` ... `{{ENNEAGRAM_PCT_9}}` | score/max_score*100 | 各类型百分比（0-100） |

### MBTI 占位符

| 占位符 | 来源 | 说明 |
|--------|------|------|
| `{{MBTI_TYPE}}` | results.mbti.type | 如"INTJ" |
| `{{MBTI_LABEL}}` | MBTI 类型中文标签 | 如"建筑师" |
| `{{MBTI_SCORE_E}}` ... `{{MBTI_SCORE_P}}` | results.mbti.dimensions | 各维度原始分 |
| `{{MBTI_PCT_E}}` ... `{{MBTI_PCT_P}}` | score/max*100 | 各维度百分比 |

### 霍兰德占位符

| 占位符 | 来源 | 说明 |
|--------|------|------|
| `{{HOLLAND_CODE}}` | results.holland.code | 如"AIS" |
| `{{HOLLAND_LABEL}}` | 代码中文标签 | 如"艺术·研究·社会" |
| `{{HOLLAND_SCORE_R}}` ... `{{HOLLAND_SCORE_C}}` | results.holland.scores | 各类型原始分 |
| `{{HOLLAND_PCT_R}}` ... `{{HOLLAND_PCT_C}}` | score/max*100 | 各类型百分比 |

### 盖洛普占位符

| 占位符 | 来源 | 说明 |
|--------|------|------|
| `{{GALLUP_DOMAIN_CN}}` | GALLUP_DOMAIN_NAMES[top_domain] | 如"战略思维" |
| `{{GALLUP_THEMES_CN}}` | top_themes 前3中文 | 如"分析、学习、成就" |
| `{{GALLUP_SCORE_EXEC}}` ... `{{GALLUP_SCORE_STRAT}}` | results.gallup.domains | 四领域原始分 |
| `{{GALLUP_PCT_EXEC}}` ... `{{GALLUP_PCT_STRAT}}` | score/max*100 | 四领域百分比 |
| `{{GALLUP_THEME_TAGS}}` | top_themes 前5 → `<span class="theme-tag">` HTML | 主题标签 |

### 免费简版专属占位符

| 占位符 | 来源 | 说明 |
|--------|------|------|
| `{{FREE_SUMMARY}}` | scorer.generate_free_summary() | 简要解读文字 |

### 付费深度版专属占位符

| 占位符 | 来源 | 说明 |
|--------|------|------|
| `{{RADAR_POINTS}}` | 雷达图5个顶点坐标 | SVG polygon points |
| `{{ENNEAGRAM_ANALYSIS}}` | AI 生成 | 九型深度解读（HTML） |
| `{{MBTI_ANALYSIS}}` | AI 生成 | MBTI 深度分析（HTML） |
| `{{HOLLAND_ANALYSIS}}` | AI 生成 | 霍兰德职业分析（HTML） |
| `{{GALLUP_ANALYSIS}}` | AI 生成 | 盖洛普优势分析（HTML） |
| `{{CROSS_ANALYSIS}}` | AI 生成 | 四体系综合交叉解读（HTML） |
| `{{SYNERGY_POINTS}}` | AI 生成 | 协同亮点内容 |
| `{{TENSION_POINTS}}` | AI 生成 | 关键张力内容 |
| `{{CAREER_LIST}}` | AI 生成 | 职业推荐列表（`<li>` HTML） |
| `{{IF_LIFECYCLE}}` / `{{/IF_LIFECYCLE}}` | 条件块 | 有 birth_date 时包含 |
| `{{BIRTH_DATE}}` | profile.birth_date | YYYY-MM-DD |
| `{{LIFECYCLE_CURRENT}}` | AI 生成 | 当前发展阶段定位（HTML） |
| `{{LIFECYCLE_FOCUS}}` | AI 生成 | 近三年专注方向（HTML） |
| `{{LIFECYCLE_PITFALL}}` | AI 生成 | 阶段性格避坑提醒（HTML） |
| `{{LIFECYCLE_CROSS}}` | AI 生成 | 与四体系交叉验证（HTML） |

## 中文映射表

### MBTI 类型标签

```
INTJ=建筑师, INTP=逻辑学家, ENTJ=指挥官, ENTP=辩论家,
INFJ=提倡者, INFP=调停者, ENFJ=主人公, ENFP=竞选者,
ISTJ=物流师, ISFJ=守卫者, ESTJ=总经理, ESFJ=执政官,
ISTP=鉴赏家, ISFP=探险家, ESTP=企业家, ESFP=表演者
```

### 霍兰德代码标签

```
R=实际型, I=研究型, A=艺术型, S=社会型, E=企业型, C=常规型
```

### 用户角色中文映射

```
student-junior-high=初中生, student-senior-high=高中生,
student-undergrad=本科生, student-grad=硕士生, student-phd=博士生,
employed=在职人士, freelancer=自由职业者, entrepreneur=创业者,
parent=家长, job-seeker=求职者
```

### 测评目的中文映射

```
career-planning=职业规划, study-direction=学习方向选择,
study-abroad-planning=留学规划, graduate-school-planning=考研/保研规划,
self-exploration=自我探索, relationship-insight=人际关系洞察,
leadership-growth=领导力成长, entrepreneur-fit=创业适配评估,
academic-stress-relief=学业压力舒缓, parent-understanding-child=了解孩子
```

## 生成流程

### 免费简版报告

1. 调用 `scorer.score_answers(questions, answers)` 获取 results
2. 调用 `scorer.generate_free_summary(results, profile)` 获取简评
3. 加载 `result-simple.html` 模板
4. 替换所有占位符（得分 + 百分比 + 简评）
5. 输出最终 HTML

### 付费深度版报告

1. 同免费版步骤 1，获取 results
2. 调用 `ai_analyzer.generate_detailed_analysis(results, profile)` 获取 AI 解读
3. 加载 `report-detailed.html` 模板
4. 替换通用占位符（同免费版）
5. 替换分析占位符（AI 生成的 HTML 内容直接插入）
6. 计算雷达图坐标（5 个体系各取一个代表性得分，映射到 0-120 的半径范围）
7. 生成主题标签 HTML（`<span class="theme-tag">主题名</span>`）
8. 生成职业推荐列表 HTML（`<li><span class="career-icon">💼</span>职业名</li>`）
9. 如有 birth_date，保留生涯发展时机建议章节；否则删除 `{{IF_LIFECYCLE}}...{{/IF_LIFECYCLE}}` 整块
10. 输出最终 HTML

## 雷达图坐标计算

详细模板中的雷达图是 5 边形（九型、MBTI、霍兰德、盖洛普、综合）。
圆心 (150,150)，最大半径 120。5 个顶点方向：

```
九型:   (150, 30)   — 正上方
MBTI:   (254, 105)  — 右上
霍兰德: (214, 240)  — 右下
盖洛普: (86, 240)   — 左下
综合:   (46, 105)   — 左上
```

每个体系的"代表分"计算方式：
- 九型：main_type 得分 / 所有类型最高可能得分 × 100
- MBTI：4 个维度的倾向强度平均值（每对取 |高-低| / (高+低) × 100）
- 霍兰德：top1 得分 / 所有类型最高可能得分 × 100
- 盖洛普：top_domain 得分 / 所有领域最高可能得分 × 100
- 综合：前四个的平均值

坐标公式：`point = center + direction * (score / 100 * max_radius)`

## AI 分析内容格式要求

AI 生成的分析内容直接插入 HTML，需要是合法的 HTML 片段：
- 段落用 `<p>` 包裹
- 加粗用 `<strong>`
- 斜体用 `<em>`
- 列表用 `<ul><li>` 或 `<ol><li>`
- 不要使用 `<h1>` — 模板已有标题层级
- 不要使用 `<html>` / `<body>` 等外壳标签

## 退化处理

- 某体系得分为 0 → 百分比显示 0%，不影响其他体系
- AI 分析调用失败 → 对应章节显示"AI 分析暂时不可用，请稍后重试"
- 无 birth_date → 删除生涯发展时机建议章节整块
- 部分题目未答 → 在报告底部添加提示"本次作答 X/100 题，结果置信度可能受影响"

## 生涯发展时机建议章节（可选）说明

**位置**：四体系综合交叉解读之后。

**触发条件**：用户 profile 含 `birth_date`（YYYY-MM-DD）。

**呈现原则**（重要）：
- 该章节是**辅助性参考视角**，与前面四体系评估**交叉印证**，不是独立结论
- 章节标题为"生涯发展时机建议"，**不出现**"八字"、"命理"、"五行"、"紫微"、"占星"等字眼
- 内容用现代生涯规划语言表述（"发展阶段"、"专注方向"、"避坑提醒"），避免玄学化措辞
- 4 个子小标题：
  1. 当前发展阶段定位
  2. 近三年专注方向
  3. 阶段性格避坑提醒
  4. 与四体系交叉验证（必须包含——把"时机建议"与 MBTI/九型/霍兰德/盖洛普四体系相互印证）

**AI 生成要点**：
- 子标题固定，不要自由发挥
- 每个子内容 80-150 字
- 数字和方向要从四体系已有结果出发推论，避免凭空断言
- 与四体系交叉验证部分必须有具体引用（如"这与您 MBTI 中的 J（判断倾向）形成呼应"）
- 语气保持冷静、专业，避免"命"、"注定"等词

## 不适用场景

- 题库出题（属"出题 skill"）
- 筛选题目（属"筛选 skill"）
- 支付处理（属支付系统）
