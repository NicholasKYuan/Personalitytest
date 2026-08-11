# 四体系融合题库结构（Enneagram + MBTI + Holland + Gallup）

> 母题库共 1500 题。**每道题均为融合题**——同时映射九型人格、MBTI、霍兰德、盖洛普优势四个体系中至少 2 个的维度倾向，理想 3-4 个。
> 题库按**主题类别**组织，10 个类别各约 150 题。

---

## 一、四体系维度速查

### 1. 九型人格（Enneagram）
- 9 型：1完美 / 2助人 / 3成就 / 4浪漫 / 5观察 / 6怀疑 / 7享乐 / 8挑战 / 9平和
- 三元中心：思维(5,6,7) / 情感(2,3,4) / 本能(8,9,1)

### 2. MBTI
- 4 维度：E/I（能量）/ S/N（信息）/ T/F（决策）/ J/P（生活）
- 16 型组合

### 3. 霍兰德职业兴趣（RIASEC）
- 6 类型：R现实 / I研究 / A艺术 / S社会 / E企业 / C常规

### 4. 盖洛普优势（CliftonStrengths）

#### 4 大领域（主映射，score key 用这 4 个）
| 领域 | 英文 key | 含义 |
|------|----------|------|
| 执行力 | `gallup.executing` | 把事做成、推进落地 |
| 影响力 | `gallup.influencing` | 掌控局面、说服带动他人 |
| 关系建立 | `gallup.relationship_building` | 建立稳固联结、团队凝聚 |
| 战略思维 | `gallup.strategic_thinking` | 吸收分析信息、做决策 |

#### 34 主题（子维度，通过题目 `gallup_themes` 字段辅助标注）
- **执行力**：Achiever成就 / Arranger统筹 / Belief信仰 / Consistency一致 / Deliberative审慎 / Discipline纪律 / Focus专注 / Responsibility责任 / Restorative排难
- **影响力**：Activator行动 / Command统率 / Communication沟通 / Competition竞争 / Maximizer完美 / Self-Assurance自信 / Significance追求 / Woo取悦
- **关系建立**：Adaptability适应 / Connectedness关联 / Developer伯乐 / Empathy体谅 / Harmony和谐 / Includer包容 / Individualization个别 / Positivity积极 / Relator交往
- **战略思维**：Analytical分析 / Context回顾 / Futuristic前瞻 / Ideation理念 / Input搜集 / Intellection思维 / Learner学习 / Strategic战略

> 设计取舍：34 主题作为 score key 会过碎且单题难以精确映射，故用 4 领域做主映射；题目可额外用 `gallup_themes` 数组标注候选主题（如 `["achiever", "focus"]`），用于后续细化用户的 Top 5-10 优势识别。

---

## 二、10 个主题类别（每类约 150 题）

| 编号 | 类别 | 主题范围 |
|------|------|----------|
| C1 | interpersonal-relationship 人际关系 | 社交模式、亲密关系、家庭、群体角色 |
| C2 | decision-making 决策判断 | 选择风格、风险偏好、信息收集方式 |
| C3 | stress-response 压力应对 | 挫折反应、情绪调节、自我恢复 |
| C4 | motivation-value 动机价值 | 内驱力、价值观、意义感 |
| C5 | learning-cognition 学习认知 | 学习风格、信息处理、好奇心方向 |
| C6 | work-career 工作职业 | 工作偏好、职业动机、协作方式 |
| C7 | emotion-self 情绪自我 | 情绪觉察、自我认知、内省 |
| C8 | action-habit 行动习惯 | 执行力、计划性、节奏感 |
| C9 | future-vision 未来愿景 | 长远视角、目标设定、可能性想象 |
| C10 | conflict-choice 冲突选择 | 矛盾处理、取舍优先、强迫选择 |

---

## 三、融合题设计原则

**每道题至少映射 2 个体系**，理想 3-4 个。维度倾向通过选项 `score` 字段表达，key 形如：
- `enneagram.type1` ~ `enneagram.type9`
- `mbti.E` / `mbti.I` / `mbti.S` / `mbti.N` / `mbti.T` / `mbti.F` / `mbti.J` / `mbti.P`
- `holland.R` / `holland.I` / `holland.A` / `holland.S` / `holland.E` / `holland.C`
- `gallup.executing` / `gallup.influencing` / `gallup.relationship_building` / `gallup.strategic_thinking`

题目可选 `gallup_themes` 字段（数组）标注候选主题，用于细化优势识别。

### 各类别的典型跨体系映射（出题锚点，非硬约束）

| 类别 | 九型 | MBTI | 霍兰德 | 盖洛普领域 |
|------|------|------|--------|------------|
| 人际关系 | 2/9/8 | E/I, T/F | S/E | 关系建立 / 影响力 |
| 决策判断 | 6/8/3 | T/F, J/P | E/C | 战略思维 / 执行力 |
| 压力应对 | 6/4/7 | T/F | I | 执行力（排难）/ 战略思维 |
| 动机价值 | 3/1/4 | T/F | E/A | 影响力 / 关系建立 |
| 学习认知 | 5/7 | S/N | I/A | 战略思维（学习/输入）|
| 工作职业 | 3/8/9 | J/P | E/C/R | 执行力 / 影响力 |
| 情绪自我 | 4/2 | T/F | A/S | 关系建立（体谅/和谐）|
| 行动习惯 | 1/3/7 | J/P | C/E | 执行力（成就/纪律）|
| 未来愿景 | 7/4/3 | S/N | A/E | 战略思维（前瞻）|
| 冲突选择 | 8/9/6 | T/F, J/P | E/S | 影响力（统率）/ 关系建立（和谐）|

### 出题质量要求
1. **避免社会赞许性偏差**：选项不要全"正面"，给中性/负向倾向同等表达空间
2. **题干简洁**：单题 ≤ 30 字，避免双关和复合句
3. **选项区分度**：不同选项的 score 模式应有明显差异
4. **情境具体**：用具体场景而非抽象概念（"开会时被当众反驳" > "面对冲突时"）
5. **盖洛普映射克制**：不要每题都强行映射 gallup；当题目行为确实反映某领域倾向时再映射，避免稀释优势识别信号

---

## 四、筛选 100 题的原则

**不按体系配额**。改为：

### 1. 类别覆盖（多样性）
10 个主题类别每类至少 8 题，剩余 20 题按用户状态加权补足。

### 2. 维度覆盖（结果可计算）

| 体系 | 最低覆盖要求 |
|------|--------------|
| 九型人格 | 9 型每型 ≥ 5 题有 score 贡献 |
| MBTI | 4 维度每极 ≥ 4 题有 score 贡献 |
| 霍兰德 | 6 类型每型 ≥ 7 题有 score 贡献 |
| 盖洛普 | 4 领域每领域 ≥ 8 题有 score 贡献；理想情况下能汇总出用户的 Top 5-10 候选主题 |

### 3. 状态匹配（核心筛选信号，权重 ~50%）
用户 profile 的 `purpose` + `current_state` + `decision_horizon` + `role` 与题目 `applicable_states` 匹配度。

### 4. 难度分布
难度 2 约 30 题、3 约 45 题、4 约 20 题、5 约 5 题。

### 5. 反向计分题
至少 10 题为 `reverse=true`。

### 6. 排序
按"类别交错 + 难度递增"排列，避免连续同类同难度。