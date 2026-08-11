# 第二轮审核报告 — 424 题（Q0001-Q0424）

审核人：砚（Kimi-K3） · 2026-08-11
范围：batch01(124) + batch02(100) + batch03(100) + batch04(100)

## 审核结论

**复验 0 问题，全部通过。424 题定稿为当前基准库。**

## 本轮发现的问题与修复

| # | 问题 | 涉及 | 严重度 | 修复方式 |
|---|------|------|--------|----------|
| 1 | Likert式题目 scale 误标 forced-choice | 36 题 | 🟡 结构 | 统一改 `likert-4`（schema 同步补枚举） |
| 2 | 场景题误标 reverse=true | Q0325/Q0335/Q0345/Q0375 | 🟡 标记 | reverse→false（真 reverse=36 题 Likert 式） |
| 3 | 题干重复「如果你的人生只剩一年」 | Q0237 vs Q0337 | 🔴 内容 | Q0337 重写为「两个人生目标间放弃一个」 |
| 4 | 有 gallup score 但缺 themes 标注 | 62 题 | 🟡 辅助 | 按类别×领域主题池自动补齐 |
| 5 | themes 与 score 领域不呼应 | Q0007/Q0104 | 🟡 辅助 | Q0007→[woo,intellection]；Q0104 补 gallup 映射 |
| 6 | 主题名误当 score key（gallup.futuristic 等） | Q0209/Q0210/Q0212/Q0213/Q0219 | 🔴 结构 | 转换为领域 key，主题名并入 themes |

## 澄清：reverse 题"无负分"不是 bug

Likert 式 reverse 题采用**反向措辞 + 对极映射**设计：
认同负向陈述 → 计负极特质（如 Q0101 认同"不喜成为焦点"→ mbti.I），
否认 → 计正极特质。计分无需负值，`reverse=true` 仅作元标记。
4 道场景题是真误标，已修正。

## 定稿指标

| 指标 | 值 |
|------|-----|
| 总题数 | 424（Q0001-Q0424） |
| scale | forced-choice 388 / likert-4 36 |
| reverse | 36 题（全部 Likert 式） |
| 难度 | 1:36 / 2:116 / 3:157 / 4:80 / 5:35 |
| 题干重复 | 0 |
| 空 score / 非法 key / 越界 | 0 |
| themes 合法性+呼应 | 100% |

## 新增避坑规则（并入第一批的 10 条）

11. **scale 字段必须反映真实作答形态**：4 点认同度题用 `likert-4`，场景选择题用 `forced-choice`
12. **reverse=true 仅用于 Likert 式负向陈述题**，场景题永不为 reverse
13. **gallup score key 只允许 4 领域名**，主题名只能出现在 `gallup_themes`
14. **出题后必须跑题干去重检查**（Q0237/Q0337 是同义重写时撞车）
15. **有 gallup score 的题必须标注 gallup_themes**，且至少一个主题的领域与 score 呼应
16. **写批后必跑自动校验脚本**：systems 同步 + key 合法性 + themes 呼应，一并过
