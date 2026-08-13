---
name: personality-test-selector
summary: 从 2117 四体系融合题库中，按用户个人信息筛选出适配当前状态的 120 题测评卷
description: |
  星耀启程人格测评的筛选 skill。输入用户 profile（年龄/角色/测评目的/当前状态），
  从 2000 道融合题（九型人格 + MBTI + 霍兰德 + 盖洛普 四体系题目级融合）中筛选 120 题，
  保证四体系全部维度可计算，输出可直接作答的测评卷 JSON。
  触发词：筛选题目、生成测评卷、选 120 题、个性化测评、测评选题。
read_when:
  - 需要根据用户信息生成个性化测评卷
  - 需要校验测评卷的四体系维度覆盖
---

# personality-test-selector

## 用途

给定用户 profile，产出 120 题个性化测评卷。一次作答即可计算：
- 九型人格主型 + 侧翼参考
- MBTI 四字母类型
- 霍兰德职业代码（前 3 位）
- 盖洛普 4 领域得分 + Top 优势主题候选

## 文件位置

- 题库：`question-bank/items.jsonl`（2000 题，每题含四体系 score 映射）
- 题库结构：`question-bank/schema.json` + `question-bank/taxonomy.md`
- 用户字段：`selector/profile-schema.json`
- 算法说明：`selector/select-logic.md`
- 可执行筛选器：`selector/selector.py`

## 调用流程

### 1. 收集用户 profile

必填三项：`age`、`role`、`purpose`（枚举见 profile-schema.json）。
推荐补填：`current_state`、`decision_horizon`、`birth_date`（为后续八字解读预留）。

若用户只给自然语言描述（如"我 22 岁大四，纠结考研还是工作"），先映射为 schema 字段：
- role: `student-undergrad`
- purpose: `career-planning`（考研 vs 就业 = 职业规划分叉）
- current_state: `transition`

### 2. 执行筛选

```bash
python selector/selector.py \
  --profile <profile.json> \
  --bank question-bank/items.jsonl \
  --out <output.json>
```

### 3. 校验输出

输出 JSON 自带 `coverage_report.checks`，必须全部 `true`：
- `enneagram_all_types>=5` — 九型每型至少 5 题有贡献
- `mbti_all_poles>=4` — MBTI 每极至少 4 题
- `holland_all_types>=2(R>=1)` — 霍兰德每型至少 2 题（R型至少 1 题，因题库偏少）
- `gallup_all_domains>=8` — 盖洛普每领域至少 8 题
- `reverse>=12` — 反向题至少 12 题（一致性检测用）

若有 `false`：向用户说明"该维度样本偏少，对应结果置信度较低"，或重跑筛选。

### 4. 交付测评卷

输出 JSON 中 `questions` 数组即 120 题作答序列（已按类别交错 + 难度递增排序），
`selection_reasons` 提供每题一句话选择理由（可向用户展示筛选的个性化依据）。

## 题库计分约定（作答后算分必读）

- 每题 4 选项，每选项 `score` 是 `{维度key: 分值}` 映射，分值范围 -3..3
- 维度 key 四类前缀：`enneagram.type1-9`、`mbti.E/I/S/N/T/F/J/P`、`holland.R/I/A/S/E/C`、`gallup.executing/influencing/relationship_building/strategic_thinking`
- `scale=likert-4` 的题（选项为"非常符合…完全不符合"）已内置反向映射，`reverse=true` 仅元标记，**无需额外反转**
- 用户选某选项 → 把该选项 score 累加到各维度总分
- 九型取总分最高型为主型；MBTI 每对维度取高分极；霍兰德取前 3 型组代码；盖洛普取 4 领域排序 + `gallup_themes` 频次 Top 主题

## 退化处理

- profile 缺必填字段 → 拒绝执行，提示补哪项
- 某维度覆盖检查失败 → 报告中标注低置信度，不要静默通过
- 题库文件缺失/损坏 → 直接报错，不要编造题目

## 不适用场景

- 结果解读（属后续"解读 skill"，本项目第二阶段）
- 八字排盘解读（第三阶段，`birth_date` 本阶段仅收集）
