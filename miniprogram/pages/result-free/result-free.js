/**
 * pages/result-free/result-free.js — 免费结果页
 *
 * 展示四体系核心结论 + 雷达图 + 免费简述 + 模糊预览，引导付费解锁完整报告。
 * 数据来源：utils/storage 中 KEYS.RESULTS（quiz 提交后写入的 submit 返回）。
 */
const storage = require('../../utils/storage')
const labels = require('../../utils/labels')

/* 四体系 Tab 与雷达配色 */
const TABS = [
  { key: 'enneagram', label: '九型人格', color: '#E94560' },
  { key: 'mbti', label: 'MBTI', color: '#8B5CF6' },
  { key: 'holland', label: '霍兰德', color: '#3B82F6' },
  { key: 'gallup', label: '盖洛普', color: '#10B981' }
]

/** 免费报告预览片段（模糊区） */
const PREVIEWS = [
  { title: '九型人格 · 内在动机', text: '你的深层动机是「被欣赏与认可」…' },
  { title: 'MBTI · 认知功能', text: '你习惯先定目标再找路径，擅长从复杂信息中提炼趋势…' },
  { title: '霍兰德 · 适配职业', text: '在需要统筹与表达的位置上最能发挥你的优势…' },
  { title: '四体系交叉解读', text: '动机、认知、兴趣、优势形成了完整的个人发展闭环…' }
]

/** 付费价值清单 */
const VALUES = [
  '九型 / MBTI / 霍兰德 / 盖洛普 四体系深度解读',
  '10,000+ 字 AI 个性化分析报告',
  '交叉协同优势与潜在张力点',
  '职业方向与成长路径建议',
  '传统易学视角的辅助参考'
]

Page({
  data: {
    tabs: TABS,
    activeTab: 'enneagram',
    radarItems: [],
    radarColor: TABS[0].color,
    radarSize: 300,
    cards: [],
    freeSummary: '',
    previews: PREVIEWS,
    values: VALUES,
    paid: false
  },

  onLoad() {
    const data = storage.getResults()
    if (!data || !data.results) {
      wx.redirectTo({ url: '/pages/index/index' })
      return
    }

    this.submitData = data
    this.results = data.results

    // 雷达图画布尺寸：适配屏幕宽度
    try {
      const win = wx.getSystemInfoSync().windowWidth
      this.setData({ radarSize: Math.min(win - 48, 340) })
    } catch (e) {
      this.setData({ radarSize: 300 })
    }

    this.setData({
      paid: !!data.paid,
      freeSummary: data.free_summary || this.buildFallbackSummary(),
      cards: this.buildCards()
    })
    this.buildRadar('enneagram')
  },

  onShow() {
    // 从支付页返回时刷新付费状态（若已支付则更新 CTA）
    const data = storage.getResults()
    if (data && data.paid && !this.data.paid) {
      this.setData({ paid: true })
    }
  },

  /* ---------- 雷达图 ---------- */
  buildRadar(key) {
    const r = this.results
    if (!r || !r[key]) return
    let items = []

    if (key === 'enneagram') {
      const scores = r.enneagram.scores || {}
      items = Object.keys(scores).map((k, i) => ({
        label: `${i + 1}号`,
        value: scores[k]
      }))
    } else if (key === 'mbti') {
      const d = r.mbti.dimensions || {}
      items = ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P'].map((k) => ({
        label: k,
        value: d[k]
      }))
    } else if (key === 'holland') {
      const s = r.holland.scores || {}
      items = ['R', 'I', 'A', 'S', 'E', 'C'].map((k) => ({
        label: k,
        value: s[k]
      }))
    } else if (key === 'gallup') {
      const d = r.gallup.domains || {}
      items = Object.keys(d).map((k) => ({
        label: labels.GALLUP_DOMAINS[k] || k,
        value: d[k]
      }))
    }

    const tab = TABS.find((t) => t.key === key) || TABS[0]
    this.setData({
      activeTab: key,
      radarItems: items,
      radarColor: tab.color
    })
  },

  onTabTap(e) {
    const key = e.currentTarget.dataset.key
    if (key && key !== this.data.activeTab) this.buildRadar(key)
  },

  /* ---------- 结果卡片 ---------- */
  buildCards() {
    const r = this.results
    const cards = []

    // 九型人格
    const en = r.enneagram || {}
    const enNum = en.main_type
    cards.push({
      key: 'enneagram',
      title: '九型人格',
      color: '#E94560',
      type: `${enNum}号 · ${en.type_name || labels.ENNEAGRAM_NAMES[enNum] || ''}`,
      desc: labels.ENNEAGRAM_DESC[enNum] || ''
    })

    // MBTI
    const mb = r.mbti || {}
    cards.push({
      key: 'mbti',
      title: 'MBTI',
      color: '#8B5CF6',
      type: mb.type || '—',
      desc: labels.MBTI_DESC[mb.type] || ''
    })

    // 霍兰德
    const ho = r.holland || {}
    const code = ho.code || ''
    const hoNames = String(code)
      .split('')
      .map((c) => labels.HOLLAND_NAMES[c])
      .filter(Boolean)
      .join('·')
    cards.push({
      key: 'holland',
      title: '霍兰德',
      color: '#3B82F6',
      type: code || '—',
      desc: hoNames || ''
    })

    // 盖洛普
    const ga = r.gallup || {}
    const themes = (ga.top_themes || []).map((t) => labels.GALLUP_THEMES[t]).filter(Boolean)
    cards.push({
      key: 'gallup',
      title: '盖洛普',
      color: '#10B981',
      type: labels.GALLUP_DOMAINS[ga.top_domain] || ga.top_domain || '—',
      desc: [labels.GALLUP_DOMAIN_DESC[ga.top_domain], themes.length ? `优势：${themes.join('、')}` : '']
        .filter(Boolean)
        .join('；')
    })

    return cards
  },

  /* ---------- 兜底简述（后端未返回 free_summary 时） ---------- */
  buildFallbackSummary() {
    const r = this.results || {}
    const parts = []
    if (r.enneagram) {
      parts.push(
        `${r.enneagram.main_type}号 ${r.enneagram.type_name || labels.ENNEAGRAM_NAMES[r.enneagram.main_type] || ''}`
      )
    }
    if (r.mbti) parts.push(r.mbti.type)
    if (r.holland) parts.push(r.holland.code)
    if (r.gallup) {
      parts.push(labels.GALLUP_DOMAINS[r.gallup.top_domain] || r.gallup.top_domain)
    }
    return `你的四体系测评结果：${parts.join(' / ')}。解锁完整报告，获取深度解读与个性化建议。`
  },

  /* ---------- 付费引导 ---------- */
  onUnlock() {
    if (this.data.paid || (this.submitData && this.submitData.paid)) {
      // 已支付 → 直接进完整报告
      wx.redirectTo({ url: '/pages/result-full/result-full' })
      return
    }
    const sessionId = (this.submitData && this.submitData.session_id) || ''
    wx.navigateTo({
      url: `/pages/pay/pay${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`
    })
  },

  onShareAppMessage() {
    return {
      title: '测一测你的人格画像，发现你的独特光芒',
      path: '/pages/index/index'
    }
  }
})
