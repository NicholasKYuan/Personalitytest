/**
 * mock.js — 前端独立预览用 Mock 数据
 *
 * 当 utils/config.js 中 USE_MOCK=true 时，utils/api.js 走这里，不发起真实网络请求。
 * 覆盖关键流程：login / session(120题) / submit(四体系结果) / order / status / report/detail。
 */

const config = require('./config')
const { GALLUP_DOMAINS, GALLUP_THEMES } = require('./labels')

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/* ============================================================
   120 题样本：由 12 个模板循环生成，保证前端可独立走完答题流程
   ============================================================ */
const LIKERT_OPTIONS = ['完全符合', '比较符合', '不太符合', '完全不符']

const TEMPLATES = [
  { category: 'interpersonal-relationship', scale: 'forced-choice', stem: '聚会中认识新朋友，我更倾向于', options: ['主动找话题，让场面热闹起来', '观察一会儿，等合适时机再加入', '留意有没有落单的人，去陪 ta', '先找熟人，跟熟人待在一起'] },
  { category: 'decision-making', scale: 'forced-choice', stem: '面临重大选择时，我通常', options: ['快速拍板，边做边调整', '反复权衡各种可能', '咨询身边信任的人', '等到不得不决定时才定'] },
  { category: 'stress-response', scale: 'likert-4', stem: '压力大的时候，我会选择先解决问题再休息', options: LIKERT_OPTIONS },
  { category: 'motivation-value', scale: 'forced-choice', stem: '最能让我感到满足的是', options: ['把目标做成、做出成绩', '帮到别人、被需要', '学到新东西、想明白事', '和大家打成一片'] },
  { category: 'learning-cognition', scale: 'forced-choice', stem: '学习新知识时，我更喜欢', options: ['先看整体框架再深入细节', '从具体例子入手慢慢总结', '边做边学、在实践中掌握', '和同学讨论着学'] },
  { category: 'work-career', scale: 'forced-choice', stem: '选择工作时，我最看重', options: ['成长空间和晋升路径', '薪酬待遇和稳定性', '兴趣和创造力发挥', '团队氛围和人际关系'] },
  { category: 'emotion-self', scale: 'likert-4', stem: '我经常能察觉到自己情绪的细微变化', options: LIKERT_OPTIONS },
  { category: 'action-habit', scale: 'forced-choice', stem: '对于计划中的事情，我', options: ['严格按计划推进', '计划只做参考，随机应变', '喜欢列计划但常被意外打断', '更倾向跟着感觉走'] },
  { category: 'future-vision', scale: 'forced-choice', stem: '谈到未来三年，我更期待', options: ['事业上有一个清晰的里程碑', '找到真正热爱并擅长的事', '生活稳定、家庭和睦', '探索更多的可能性'] },
  { category: 'conflict-choice', scale: 'forced-choice', stem: '与他人意见不合时，我会', options: ['直接表达并坚持立场', '先听对方说完再回应', '暂时回避，等情绪平复', '找中间人帮忙协调'] },
  { category: 'interpersonal-relationship', scale: 'likert-4', stem: '我愿意主动结识不同圈子的人', options: LIKERT_OPTIONS },
  { category: 'motivation-value', scale: 'likert-4', stem: '即使没人监督，我也会坚持把事情做到最好', options: LIKERT_OPTIONS }
]

function pad(n) {
  return String(n).padStart(4, '0')
}

function buildQuestions(total) {
  const list = []
  for (let i = 0; i < total; i++) {
    const t = TEMPLATES[i % TEMPLATES.length]
    list.push({
      id: 'MQ' + pad(i + 1),
      stem: t.stem,
      scale: t.scale,
      options: t.options.map((text) => ({ text })),
      category: t.category,
      difficulty: (i % 3) + 1
    })
  }
  return list
}

/* ============================================================
   Mock 四体系结果（固定样本，模拟真实后端返回结构）
   ============================================================ */
const MOCK_RESULTS = {
  enneagram: {
    main_type: 3,
    type_name: '成就者',
    scores: { type1: 5, type2: 8, type3: 18, type4: 10, type5: 7, type6: 9, type7: 12, type8: 11, type9: 6 }
  },
  mbti: {
    type: 'ENTJ',
    dimensions: { E: 16, I: 6, S: 7, N: 14, T: 17, F: 5, J: 15, P: 7 }
  },
  holland: {
    code: 'EAS',
    scores: { R: 6, I: 9, A: 13, S: 11, E: 16, C: 8 }
  },
  gallup: {
    top_domain: 'executing',
    domains: { executing: 20, influencing: 13, relationship_building: 9, strategic_thinking: 16 },
    top_themes: ['achiever', 'focus', 'arranger']
  }
}

function buildFreeSummary(results, profile) {
  const name = (profile && profile.name) || '你'
  const themes = (results.gallup.top_themes || [])
    .slice(0, 3)
    .map((t) => GALLUP_THEMES[t] || t)
    .join('、')
  return (
    `${name}的九型人格主型为【${results.enneagram.main_type}号 - ${results.enneagram.type_name}】。` +
    `MBTI类型为【${results.mbti.type}】。` +
    `霍兰德职业兴趣代码为【${results.holland.code}】。` +
    `盖洛普优势主导领域为【${GALLUP_DOMAINS[results.gallup.top_domain] || results.gallup.top_domain}】。` +
    `核心优势主题包括：${themes}。` +
    `解锁深度报告，获取四体系交叉解读与AI个性化建议。`
  )
}

/* ============================================================
   Mock 完整报告章节（Markdown）
   ============================================================ */
const MOCK_SECTIONS = [
  {
    title: '九型人格深度解读',
    content: `## 3号 · 成就者

你的主型为 **3号成就者**，这一类型的人以目标感和高效执行著称。

### 核心特质

- 天生对目标敏感，习惯把大目标拆解为可执行的小步骤
- 渴望被认可，成就感往往来自外界的正向反馈
- 擅长在不同场景快速切换状态，适应力强

### 内在动机

3号的深层动机是 **被欣赏与认可**。当你看到自己的努力被看见、成绩被肯定时，会产生强烈的价值感。

### 可能的盲区

- 过度投入工作可能忽略身体与情感需求
- 目标受阻时容易陷入自我苛责

### 成长方向

学会「不为了证明而奔跑」，允许自己偶尔停下来，关注过程中的体验，而不只看结果。`
  },
  {
    title: 'MBTI深度分析',
    content: `## ENTJ · 指挥官

你的 MBTI 类型为 **ENTJ**，在十六型人格中属于「指挥官」型，是典型的战略规划者与高效执行者。

### 认知功能

- **Te（外倾思维）**：快速组织资源，追求效率与秩序
- **Ni（内倾直觉）**：从复杂信息中提炼长期趋势
- **Se（外倾感觉）**：行动果断，把握当下机会
- **Fi（内倾情感）**：内心深处保有个人价值观

### 思维模式

你习惯「先定目标，再找路径」。面对复杂局面，你会快速梳理主线、分配资源，并推动大家向前走。`
  },
  {
    title: '霍兰德职业方向',
    content: `## EAS · 企业型主导

你的霍兰德职业兴趣代码为 **EAS**（企业型-艺术型-社会型）。

### 适配方向

1. 企业管理、项目负责人、产品经理
2. 市场营销、销售管理、商务拓展
3. 创意策划、品牌运营、内容创作

### 发展建议

把「影响力」与「创造力」结合，在需要统筹与表达的位置上最能发挥你的优势。`
  },
  {
    title: '盖洛普优势发挥',
    content: `## 执行力 · 主导领域

你的盖洛普优势主导领域为 **执行力**，核心主题：成就、专注、统筹。

### 优势放大

- 成就主题让你持续向前推进
- 专注主题让你在关键任务上保持深度投入
- 统筹主题让你善于协调多方资源

### 盲区补足

适度把舞台交给他人，练习授权，避免所有事情都亲力亲为。`
  },
  {
    title: '四体系综合交叉解读',
    content: `## 你的独特协同优势

把四个体系放在一起看，你的画像高度一致：

- 九型【3号 成就者】→ 内在动机：追求成就
- MBTI【ENTJ】→ 认知方式：战略思维
- 霍兰德【EAS】→ 职业兴趣：影响他人
- 盖洛普【执行力】→ 优势表现：推动落地

### 协同点

动机、认知、兴趣、优势形成了「目标-策略-表达-执行」的完整闭环，这让你在需要 **从 0 到 1 搭建局面** 的岗位上极具竞争力。

### 张力点

当外部认可不足时，你的自我怀疑可能被放大；建议建立「内在标尺」，不完全依赖他人评价。`
  },
  {
    title: '传统易学结合解读',
    content: `## 命理与心理的呼应

根据你填写的出生信息，传统易学视角下你的命局「火土偏旺」，对应行动力与承载力的结合，与你在测评中表现出的高执行力、高目标感互相印证。

此类格局「宜动不宜静」，适合持续尝试新领域，并在实践中积累沉淀，避免长时间停留在空想阶段。`
  }
]

/* ============================================================
   对外 Mock API（与真实接口签名一致）
   ============================================================ */
const mockApi = {
  login() {
    return delay(200).then(() => ({
      token: 'mock_token_' + Date.now(),
      openid: 'mock_openid_xingyao',
      is_new: true,
      expires_in: 604800
    }))
  },

  createSession(profile) {
    return delay(500).then(() => ({
      session_id: 'mock_session_' + Date.now(),
      total: config.TOTAL_QUESTIONS,
      questions: buildQuestions(config.TOTAL_QUESTIONS)
    }))
  },

  submitAnswers(sessionId, answers) {
    return delay(900).then(() => ({
      session_id: sessionId,
      results: MOCK_RESULTS,
      free_summary: buildFreeSummary(MOCK_RESULTS, { name: '你' }),
      detailed_available: true,
      paid: false
    }))
  },

  createOrder(sessionId) {
    return delay(400).then(() => ({
      order_id: 10001,
      out_trade_no: 'SXMOCK' + Date.now(),
      // paySign 固定为 MOCK_SIGN：前端据此识别「模拟支付」模式，走模拟成功流程
      pay_params: {
        appId: 'wx95a916e6c9b3d382',
        timeStamp: String(Math.floor(Date.now() / 1000)),
        nonceStr: 'mock_nonce',
        package: 'prepay_id=mock_' + sessionId,
        signType: 'RSA',
        paySign: 'MOCK_SIGN'
      },
      amount_fen: config.PRICE_FEN,
      paid: false
    }))
  },

  getReportStatus(sessionId) {
    return delay(200).then(() => ({
      payment_status: 'paid',
      report_status: 'ready',
      paid: true,
      is_ready: true
    }))
  },

  getFreeResult(sessionId) {
    return delay(300).then(() => ({
      session_id: sessionId,
      results: MOCK_RESULTS,
      free_summary: buildFreeSummary(MOCK_RESULTS, {}),
      profile: { name: '你', age: 22, role: 'student-undergrad', purpose: 'career-planning' },
      paid: false
    }))
  },

  getReportDetail(sessionId) {
    return delay(600).then(() => ({
      session_id: sessionId,
      report: {
        profile: { name: '你', age: 22, role: 'student-undergrad', purpose: 'career-planning' },
        results: MOCK_RESULTS,
        sections: MOCK_SECTIONS,
        generated_at: '2026-08-12 12:00:00',
        fallback_used: false
      }
    }))
  }
}

module.exports = mockApi
