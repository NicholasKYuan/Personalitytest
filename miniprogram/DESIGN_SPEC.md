# 星鉴人格 · 视觉设计规范（v2.0）

> 本文档为「星鉴人格测评」小程序的整体视觉美化方案，基于新 logo（白底彩虹星形线条）制定。
> 所有数值单位均为 rpx（微信小程序），可直接指导 WXSS 改造。

---

## 1. 配色方向决策

### 1.1 三方案利弊分析

**方案 A：保持深蓝黑星空系，logo 放白色圆形容器**

- 利：星空神秘感强，与"星"字呼应；现有代码改动小，仅需套 logo 容器。
- 弊：logo 白底圆形容器在深色页面上是一个刺眼的"白色补丁"，割裂感重；深蓝黑底色厚重压抑，与"发现你的独特光芒"的温暖定位不符；用户已反馈"有点丑"，说明深色系本身即问题来源，保留无法解决核心痛点。

**方案 B：转向浅色/米白系，整体明亮温暖**

- 利：与 logo 白底气质完全统一，logo 可近乎"隐形融入"页面；彩虹线条在浅色底上显色最佳；明亮温暖契合人格测评的亲和力与信任感。
- 弊：完全丢失"星空/星辰"品牌联想，Slogan 中"光芒"的视觉锚点消失；纯白底易显平庸，缺少记忆点。

**方案 C（推荐）：浅暖底 + 星光点缀，明亮系微星空**

- 以暖米白为基底（温暖、明亮、与 logo 白底统一），在页面顶部保留一层**浅色渐变光晕 + 少量星光粒子**（颜色改为彩虹色系中的暖金/紫罗兰，透明度极低），既保住"星耀"的品牌意象，又不与 logo 冲突。
- 利：logo 融入自然；品牌"星"的记忆点保留；温暖亲和、转化页信任感更强；星空元素从"底色"退为"点缀"，技术实现零门槛（WXSS 完全支持）。
- 弊：改造工作量略大于 A（需改所有文字色与卡片色），但仍在一次迭代可完成范围内。

### 1.2 决策结论

**采用方案 C：暖光星语（Warm Luminous）**

- 基调：米白暖底 + 深色墨文字，卡片纯白悬浮。
- 强调色：取自 logo 彩虹渐变中的「珊瑚红 → 紫罗兰」双色渐变，作为品牌主渐变，延续旧版红紫基因降低用户认知成本。
- 星光：以极低透明度的暖金/紫罗兰圆点 + 顶部径向光晕呈现"光芒"意象，呼应 Slogan「发现你的独特光芒」。

---

## 2. 设计规范

### 2.1 配色板（CSS 变量）

```css
page {
  /* ---- 品牌主色 ---- */
  --brand-coral: #F2545B;      /* logo 彩虹·红端，主强调色 */
  --brand-coral-deep: #E03E52; /* 珊瑚红加深，按下态/深强调 */
  --brand-violet: #8B5CF6;     /* logo 彩虹·紫端，辅强调色 */
  --brand-gradient: linear-gradient(135deg, #F2545B 0%, #8B5CF6 100%); /* 品牌主渐变 */
  --btn-gradient: linear-gradient(135deg, #D13841 0%, #8B5CF6 100%);  /* 承载白色文字的按钮渐变（起点加深，白字对比度 4.8:1 过 AA） */

  /* ---- 彩虹辅助色（取自 logo，用于标签/分类/图表） ---- */
  --rainbow-red: #F2545B;
  --rainbow-orange: #F59E0B;
  --rainbow-green: #34C77B;
  --rainbow-blue: #3B9ED8;
  --rainbow-violet: #8B5CF6;
  --rainbow-purple: #C65CF0;

  /* ---- 背景 ---- */
  --bg-page: #FAF7F2;          /* 页面基底·暖米白 */
  --bg-glow-top: #FFF3E8;      /* 顶部光晕·暖桃 */
  --bg-glow-violet: #F3EFFF;   /* 顶部光晕·浅紫 */
  --bg-card: #FFFFFF;          /* 卡片白 */
  --bg-card-soft: #FFF9F4;     /* 柔和强调卡片底 */

  /* ---- 文字 ---- */
  --text-main: #2B2622;        /* 主文字·深墨棕（比纯黑柔和） */
  --text-sub: #6E665E;         /* 次要文字·暖灰 */
  --text-muted: #756A60;       /* 辅助文字·暖灰（WCAG AA 4.93:1 on bg-page） */
  --text-onbrand: #FFFFFF;     /* 渐变按钮上的白字 */

  /* ---- 品牌色作为小字文字色（对比度 ≥ 4.5:1，替代直接用彩虹色作小字） ---- */
  --text-coral: #CD3540;       /* 链接/强调文字·珊瑚红加深 */
  --text-violet: #6D3FD4;      /* 紫罗兰加深 */
  --text-warning: #8F5A00;     /* 警示文字·琥珀加深 */
  --text-warning-deep: #92400E;/* 警示横幅正文 */

  /* ---- 徽章专用深色文字（在 10% 浅色底上对比度 ≥ 4.5:1） ---- */
  --badge-text-red: #C03A42;
  --badge-text-violet: #6D3FD4;
  --badge-text-blue: #186FA6;
  --badge-text-green: #177E4A;

  /* ---- 线条与分割 ---- */
  --border-light: #F0EAE2;     /* 浅分割线 */
  --border-card: #F3EEE7;      /* 卡片描边 */
  --border-focus: #F2545B;     /* 选中态描边 */

  /* ---- 功能色 ---- */
  --color-success: #34C77B;
  --color-warning: #F59E0B;
  --color-error: #F2545B;
  --color-info: #3B9ED8;

  /* ---- 星光点缀 ---- */
  --star-gold: rgba(245, 158, 11, 0.55);
  --star-violet: rgba(139, 92, 246, 0.45);
  --star-coral: rgba(242, 84, 91, 0.45);
}
```

**页面背景**（替换原深蓝渐变）：

```css
page {
  min-height: 100vh;
  background: linear-gradient(180deg, var(--bg-glow-top) 0%, var(--bg-page) 28%, var(--bg-page) 100%);
  color: var(--text-main);
  font-size: 28rpx;
  line-height: 1.6;
}
```

### 2.2 字体层级

| 层级 | 用途 | 字号 | 字重 | 行高 | 颜色 | 其他 |
|---|---|---|---|---|---|---|
| Display | 首页品牌名 | 56rpx | 800 | 1.2 | --text-main | letter-spacing 6rpx |
| H1 | 页面大标题（报告标题/题目） | 40–44rpx | 700 | 1.5 | --text-main | — |
| H2 | 区块标题 section-title | 34rpx | 700 | 1.4 | --text-main | 前置 8rpx 渐变竖条装饰 |
| H3 | 卡片标题 | 30rpx | 600 | 1.4 | --text-main | — |
| Body | 正文 | 28rpx | 400 | 1.7 | --text-sub | — |
| Caption | 辅助说明/来源/标签 | 24rpx | 400 | 1.5 | --text-muted | — |
| Number | 数据大字（统计/类型码） | 40–48rpx | 800 | 1.2 | 各主题色 | font-variant-numeric: tabular-nums |

字体族保持现有系统栈：`-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif`。

### 2.3 圆角规范

| 场景 | 圆角 |
|---|---|
| 大卡片 / 弹层 | 32rpx |
| 普通卡片 / 选项按钮 | 24rpx |
| 输入框 | 20rpx |
| 主按钮（胶囊） | 999rpx（全圆角） |
| 标签 / 徽章 | 999rpx |
| logo 容器 | 36rpx（圆角矩形）或 50%（圆形头像位） |

### 2.4 阴影规范（浅色系的立体感核心）

```css
/* 卡片默认 */
--shadow-card: 0 4rpx 24rpx rgba(43, 38, 34, 0.06);

/* 卡片悬浮/重要卡片 */
--shadow-card-lg: 0 12rpx 40rpx rgba(43, 38, 34, 0.10);

/* 主按钮品牌光晕 */
--shadow-brand: 0 10rpx 32rpx rgba(242, 84, 91, 0.28);

/* logo 容器 */
--shadow-logo: 0 8rpx 28rpx rgba(43, 38, 34, 0.10);
```

浅色设计禁止使用过深阴影（rgba 透明度 ≤ 0.10，品牌色光晕除外）。

### 2.5 间距系统（8rpx 基准）

| Token | 值 | 用途 |
|---|---|---|
| space-1 | 8rpx | 图标与文字微距 |
| space-2 | 16rpx | 元素内紧凑间距 |
| space-3 | 24rpx | 卡片内边距/列表项间距 |
| space-4 | 32rpx | 页面左右边距、卡片大内边距 |
| space-5 | 40rpx | 区块内分组间距 |
| space-6 | 48rpx | 区块之间间距 |
| space-8 | 64rpx | 大区块分隔 |

- 页面容器：`padding: 32rpx 32rpx 80rpx;`
- 卡片内边距：默认 `32rpx`，紧凑卡片 `24rpx 28rpx`。
- 卡片之间纵向间距：`24rpx`。

### 2.6 按钮样式

```css
/* 主按钮（胶囊渐变） */
.btn-primary {
  background: var(--btn-gradient);
  color: var(--text-onbrand);
  font-size: 34rpx;
  font-weight: 600;
  border-radius: 999rpx;
  padding: 26rpx 0;
  border: none;
  box-shadow: var(--shadow-brand);
}
.btn-primary:active {
  opacity: 0.88;
  transform: scale(0.98);
}

/* 次按钮（白底描边） */
.btn-ghost {
  background: var(--bg-card);
  color: var(--text-main);
  font-size: 30rpx;
  font-weight: 500;
  border-radius: 999rpx;
  padding: 22rpx 0;
  border: 2rpx solid var(--border-light);
  box-shadow: var(--shadow-card);
}

/* 文字按钮（弱行动） */
.btn-text {
  color: var(--text-coral);
  font-size: 28rpx;
  font-weight: 500;
  background: transparent;
}

/* 禁用态 */
button[disabled] {
  background: #EFEAE3 !important;
  color: var(--text-muted) !important;
  box-shadow: none;
  opacity: 1; /* 不再用透明度压暗，直接换色 */
}
```

### 2.7 卡片样式

```css
/* 基础卡片（替代原毛玻璃 glass-card） */
.card {
  background: var(--bg-card);
  border-radius: 32rpx;
  border: 1rpx solid var(--border-card);
  box-shadow: var(--shadow-card);
  box-sizing: border-box;
}

/* 品牌强调卡片（付费转化等） */
.card--brand {
  background: linear-gradient(160deg, #FFF1F0 0%, #F5F0FF 100%);
  border: 1rpx solid rgba(242, 84, 91, 0.18);
}

/* 区块标题带渐变竖条 */
.section-title {
  font-size: 34rpx;
  font-weight: 700;
  color: var(--text-main);
  margin: 48rpx 0 24rpx;
  padding-left: 20rpx;
  position: relative;
}
.section-title::before {
  content: '';
  position: absolute;
  left: 0; top: 8rpx; bottom: 8rpx;
  width: 8rpx;
  border-radius: 4rpx;
  background: var(--brand-gradient);
}
```

### 2.8 答题页专用组件

```css
/* ---- 进度条 ---- */
.progress-track {
  height: 12rpx;
  background: #EFE9E0;
  border-radius: 999rpx;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--brand-gradient);
  border-radius: 999rpx;
  transition: width 0.4s ease;
}

/* ---- 选项按钮 ---- */
.option-item {
  display: flex;
  align-items: center;
  padding: 30rpx 28rpx;
  background: var(--bg-card);
  border: 2rpx solid var(--border-light);
  border-radius: 24rpx;
  box-shadow: var(--shadow-card);
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}
.option-item--selected {
  border-color: var(--brand-coral);
  background: #FFF5F4;
  box-shadow: 0 6rpx 20rpx rgba(242, 84, 91, 0.14);
}
.option-mark {
  width: 44rpx; height: 44rpx;
  border-radius: 50%;
  border: 2rpx solid #E3DCD2;
  color: var(--text-muted);
  font-size: 26rpx;
}
.option-item--selected .option-mark {
  background: var(--brand-coral);
  border-color: var(--brand-coral);
  color: #fff;
}
.option-text { color: var(--text-main); font-size: 30rpx; }

/* ---- 分类徽章（彩虹色系按体系分配） ---- */
.badge-category {  /* 九型人格→珊瑚红 */
  color: var(--badge-text-red);
  background: rgba(242, 84, 91, 0.10);
  border: 1rpx solid rgba(242, 84, 91, 0.30);
}
.badge-scale {     /* MBTI→紫罗兰 */
  color: var(--badge-text-violet);
  background: rgba(139, 92, 246, 0.10);
  border: 1rpx solid rgba(139, 92, 246, 0.30);
}
/* 霍兰德→蓝 badge-text-blue，盖洛普→绿 badge-text-green，规则同上 */
```

---

## 3. 逐页面美化方案

### 3.1 index 首页

1. **背景**：page 改为 §2.1 的暖米白渐变；`.bg-stars` 保留但星星改用 `.star` 新配色（gold/violet/coral 三色轮换，尺寸 4–10rpx，透明度降低），营造"微光"而非"夜空"。
2. **logo 区**：`.logo-circle`（渐变圆形+星字）替换为真实 logo 容器（见 §4），尺寸 160×160rpx，下方 `hero-title` 改 `--text-main` 深墨色，去掉 text-shadow。
3. **Slogan**：颜色由金色 `#F59E0B` 改为 `var(--brand-coral)`，可加 1rpx 字间距。
4. **体系标签**：四个 system-tag 分别套用彩虹四色徽章样式（红/紫/蓝/绿），替代统一的红框。
5. **feature-list / review-card / stats-section**：`.glass-card` 全部替换为 `.card` 白卡；feature-dot 保留渐变圆点；review-author 改 `--text-muted`。
6. **stats 数字**：`.stat-num` 改为 `var(--brand-coral)`，divider 改 `--border-light`。
7. **底部 CTA**：主按钮不变（新渐变），`footer-tip` 改 muted；`footer-history` 改为 `.btn-text` 样式去下划线。
8. **入场节奏**：各 section 保留 fade-in，用 animation-delay 0.1s/0.2s/0.3s 做阶梯入场。

### 3.2 profile 信息填写页

1. 页面标题区：顶部加小尺寸 logo（80rpx，圆形裁切）+ 「完善个人信息」H1。
2. 表单卡片：白卡承载整个表单，输入框样式统一为：
   ```css
   .input {
     background: #FBF8F4;
     border: 2rpx solid var(--border-light);
     border-radius: 20rpx;
     padding: 24rpx 28rpx;
     font-size: 30rpx;
     color: var(--text-main);
   }
   .input--focus { border-color: var(--brand-coral); background: #fff; }
   ```
3. label：26rpx / 600 / --text-main，与输入框间距 12rpx。
4. 性别/选项类选择器：复用 quiz 的 option-item 横排紧凑版（padding 20rpx）。
5. 提交按钮：主按钮，置底；错误提示文字用 `--color-error` + 12rpx 上间距。

### 3.3 quiz 答题页

1. 进度区：进度数字左侧加小星光图标点；track/fill 按 §2.8。
2. 题目卡：改白卡（`padding: 40rpx 32rpx`），题干 H1 40rpx 深墨色，去掉白色。
3. 徽章：按体系分色（§2.8 彩虹徽章），让 120 题答题过程有色彩节奏变化。
4. 选项：按 §2.8；选中态左侧 option-mark 打勾字符 "✓" 白色。
5. 底部导航：`btn-prev` 改白底描边次按钮；`btn-submit` 保持品牌渐变；swipe-hint 用 muted。
6. 答完最后一题的提交按钮可加 `box-shadow: var(--shadow-brand)` 强调。

### 3.4 result-free 免费结果页

1. 标题：「你的专属人格画像」44rpx 深墨色，副标题 muted。
2. 雷达图卡：白卡；radar-tab 默认白底描边，`--active` 改浅珊瑚底 + 珊瑚边框 + 珊瑚文字。Canvas 雷达图配色：网格线 `#EFE9E0`，数据区 `rgba(242,84,91,0.18)` 填充 + `#F2545B` 描边，第二组数据用 `#8B5CF6`。
3. 四体系结果卡（2×2）：白卡；`.rc-type` 大字分别用四体系主题色（九型红/MBTI紫/霍兰德蓝/盖洛普绿），与徽章呼应，是本页最强视觉记忆点。
4. 免费简述卡：白卡 + H3 标题。
5. 模糊预览卡：保持 blur 处理，标题加「🔒」改用品牌色徽章「完整版专属」；背景改 `card--brand` 浅渐变提示价值感。
6. CTA 卡：`card--brand`，quote 用斜体正文色；cv-dot 保留渐变点；主按钮「解锁完整报告」+ 价格锚点用珊瑚红加粗。
7. 分享按钮：次按钮样式。

### 3.5 pay 付费转化页

1. 顶部：logo 小图 + 「解锁你的完整人格报告」H1，下方价格区：大号价格 64rpx/800 珊瑚红，划线原价 muted。
2. 权益清单：白卡，每项左侧用 ✓ 圆形渐变图标（替代圆点），逐项列完整报告内容。
3. 对比区（免费 vs 完整）：如有，用两列白卡，完整版列加 `card--brand` + 「推荐」角标（右上角渐变胶囊）。
4. 信任背书：支付安全/退款保障图标行，caption 灰字。
5. 底部固定 CTA 栏：白底 + 顶部分割线 + 主按钮，按钮文案含价格（如「立即解锁 ¥9.9」），下方 caption「微信支付 · 安全便捷」。
6. 倒计时/优惠提示（如有）：warning 色胶囊标签，不用大红闪烁。

### 3.6 result-full 完整报告页

1. 页头：祝贺语 + logo 小图，主标题「你的完整人格报告」，副标题显示生成日期 muted。
2. 报告导航锚点（如有多章节）：横向滚动胶囊标签，选中态渐变底白字。
3. 章节卡：每章一张白卡，章标题用 H2 + 渐变竖条；四体系章节标题色对应彩虹四色。
4. 图表区：条形图用品牌渐变填充；维度条形底色 `#EFE9E0`，数值 label 深墨。
5. 建议/行动清单：checklist 样式，左侧渐变 ✓ 圆图标 + 正文。
6. 页尾：分享按钮（次按钮）+ 「重新测评」文字按钮；品牌落款「星鉴人格 · 发现你的独特光芒」居中 muted。

---

## 4. Logo 集成方案

### 4.1 容器方案

logo.jpg 为白底 JPG（无透明通道），需通过容器让"白底"变成设计的一部分而非缺陷：

**方案：白底圆角矩形容器（推荐）**

logo 本身白底，直接放入白色圆角卡片中，视觉上 logo 与容器融为一体，看不出 JPG 边界：

```css
.logo-wrap {
  width: 160rpx;
  height: 160rpx;
  border-radius: 36rpx;
  background: #FFFFFF;
  box-shadow: var(--shadow-logo);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.logo-wrap image {
  width: 88%;       /* 留白边距，避免贴边 */
  height: 88%;
}
```

WXSS 中 `<image src="/assets/logo.jpg" mode="aspectFit" />`。

> 注意：新浅色背景下容器阴影极浅，logo 看起来就像"印在页面上"。若后续能拿到透明底 PNG/SVG，可去掉容器直接放置，样式已预留兼容（背景白色与页面卡片一致，不突兀）。

### 4.2 各页面 logo 摆放

| 页面 | 尺寸 | 形态 | 位置 |
|---|---|---|---|
| index 首页 | 160×160rpx | 圆角矩形 36rpx + 阴影 | hero 顶部居中，替换原 logo-circle |
| profile | 80×80rpx | 圆角矩形 24rpx | 页面顶部左侧，标题旁 |
| quiz | 不出现 | — | 答题过程保持专注，仅进度区 |
| result-free | 96×96rpx | 圆角矩形 28rpx | 报告标题上方居中 |
| pay | 96×96rpx | 圆角矩形 28rpx | 顶部价格区上方居中 |
| result-full | 80×80rpx | 圆角矩形 24rpx | 页头左侧 + 页尾落款居中 64rpx |

---

## 5. 实施清单（给前端）

1. `app.wxss`：整体替换变量区与 page 背景；`.glass-card` 重定义为白卡（类名保留，改动最小）；按钮三件套替换；`.star` 改浅色星光。
2. 各页 wxss 中所有 `#fff`/`rgba(255,255,255,…)` 文字色替换为 §2.1 文字变量。
3. index.wxml：`.logo-circle` 节点替换为 `<view class="logo-wrap"><image src="/assets/logo.jpg" mode="aspectFit"/></view>`。
4. quiz 徽章按体系加修饰类（badge--enneagram / badge--mbti / badge--holland / badge--gallup）。
5. 雷达图 JS 配色同步更新（result-free.js 中 canvas 绘制色值）。
6. 逐页对照 §3 调整间距与组件。

**禁止事项**：浅色体系下不再使用 `text-shadow` 发光、不再使用白色半透明边框、阴影透明度不超过 0.10（品牌光晕除外）。
