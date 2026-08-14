/**
 * pages/result-free/result-free.js — 免费结果页
 *
 * 展示四体系核心结论 + 雷达图 + 免费简述 + 模糊预览，引导付费解锁完整报告。
 * 数据来源（二选一）：
 *   1. quiz 提交后 → utils/storage 中 KEYS.RESULTS（本地缓存）
 *   2. 测评记录点入 → URL ?session_id=xxx → GET /api/report/free 拉取
 */
const api = require('../../utils/api')
const storage = require('../../utils/storage')
const labels = require('../../utils/labels')

// 海报配色（与设计 token 对齐；Canvas 无法读取 CSS 变量）
const POSTER_COLORS = {
  textMain: '#2B2622',
  textSub: '#6E665E',
  textMuted: '#756A60',
  coral: '#F2545B',
  coralDeep: '#D13841',
  violet: '#8B5CF6',
  blue: '#3B9ED8',
  orange: '#F59E0B',
  green: '#34C77B',
  cardBg: '#FFFFFF',
  trackBg: '#F0EAE2'
}

// 海报星光（固定坐标，保证每次生成结果一致）
const POSTER_STARS = [
  { x: 62, y: 48, r: 1.6, a: 0.35, c: '245,158,11' },
  { x: 528, y: 42, r: 1.2, a: 0.30, c: '139,92,246' },
  { x: 478, y: 108, r: 1.8, a: 0.24, c: '242,84,91' },
  { x: 104, y: 128, r: 1.0, a: 0.30, c: '59,158,216' },
  { x: 548, y: 208, r: 1.4, a: 0.22, c: '245,158,11' },
  { x: 48, y: 252, r: 1.2, a: 0.24, c: '139,92,246' },
  { x: 302, y: 34, r: 1.0, a: 0.20, c: '242,84,91' },
  { x: 198, y: 66, r: 1.3, a: 0.26, c: '59,158,216' }
]

/* 四体系 Tab 与雷达配色 */
const TABS = [
  { key: 'enneagram', label: '九型人格', color: '#F2545B' },
  { key: 'mbti', label: 'MBTI', color: '#8B5CF6' },
  { key: 'holland', label: '霍兰德', color: '#3B9ED8' },
  { key: 'gallup', label: '盖洛普', color: '#34C77B' }
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
    paid: false,
    shareImagePath: '',  // 预生成的海报路径，用于转发 imageUrl
  },

  onLoad(options) {
    const optSid = (options && options.session_id) || ''
    const cached = storage.getResults()

    // 本地缓存恰好是该会话 → 直接渲染（答题后跳转的常规路径）
    if (cached && cached.results && (!optSid || cached.session_id === optSid)) {
      this._initFromData(cached)
      return
    }

    // 测评记录点入 / 缓存是其他会话 → 按 session_id 从服务端拉取
    if (optSid) {
      api
        .getFreeResult(optSid)
        .then((res) => {
          const data = {
            session_id: optSid,
            results: res.results,
            free_summary: res.free_summary,
            paid: !!res.paid
          }
          this._initFromData(data)
          // 同步本地缓存，供 pay 页 / result-full 页兜底使用
          storage.setResults(data)
        })
        .catch((err) => {
          wx.showToast({ title: (err && err.message) || '加载失败', icon: 'none' })
          setTimeout(() => wx.redirectTo({ url: '/pages/index/index' }), 1200)
        })
      return
    }

    // 既无缓存也无 session_id → 回首页
    wx.redirectTo({ url: '/pages/index/index' })
  },

  /** 用统一数据初始化页面（雷达图 + 卡片 + 简述） */
  _initFromData(data) {
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

    // 静默预生成海报，用于转发时的 imageUrl
    this._preGenerateSharePoster()
  },

  onShow() {
    // 从支付页返回时刷新付费状态（仅当缓存属于当前会话，避免串号）
    const data = storage.getResults()
    const curSid = this.submitData && this.submitData.session_id
    if (data && data.paid && !this.data.paid && data.session_id === curSid) {
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
      color: '#F2545B',
      type: `${enNum}号·${en.type_name || labels.ENNEAGRAM_NAMES[enNum] || ''}`,
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
      color: '#3B9ED8',
      type: code || '—',
      desc: hoNames || ''
    })

    // 盖洛普
    const ga = r.gallup || {}
    const themes = (ga.top_themes || []).map((t) => labels.GALLUP_THEMES[t]).filter(Boolean)
    cards.push({
      key: 'gallup',
      title: '盖洛普',
      color: '#34C77B',
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
    const sessionId = (this.submitData && this.submitData.session_id) || ''
    if (this.data.paid) {
      // 已支付 → 直接进完整报告（带 session_id，避免 result-full 读错缓存）
      wx.redirectTo({
        url: `/pages/result-full/result-full${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`
      })
      return
    }
    wx.navigateTo({
      url: `/pages/pay/pay${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`
    })
  },

  /** 静默预生成分享缩略图（600×480 紧凑版：品牌 + 问候 + 四卡片 + 一句解读） */
  _preGenerateSharePoster() {
    if (this._posterPreparing) return
    this._posterPreparing = true
    const w = 600
    const h = 480
    const ctx = wx.createCanvasContext('posterCanvas', this)
    const C = POSTER_COLORS

    const grad = ctx.createLinearGradient(0, 0, 0, h)
    grad.addColorStop(0, '#FFF6EC')
    grad.addColorStop(0.35, '#FDF8F3')
    grad.addColorStop(1, '#F6F1FA')
    ctx.setFillStyle(grad)
    ctx.fillRect(0, 0, w, h)

    POSTER_STARS.forEach((s) => {
      ctx.beginPath()
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
      ctx.setFillStyle(`rgba(${s.c},${s.a})`)
      ctx.fill()
    })

    let y = 40
    y = this._pBrand(ctx, w, y, C)
    y = this._pGreeting(ctx, w, y, C)
    y = this._pSystemGrid(ctx, w, y, C)
    y = this._pInsightCompact(ctx, w, y, C)

    ctx.draw(false, () => {
      setTimeout(() => {
        wx.canvasToTempFilePath({
          canvasId: 'posterCanvas',
          x: 0, y: 0, width: w, height: h,
          success: (res) => {
            this.setData({ shareImagePath: res.tempFilePath })
          },
          complete: () => {
            this._posterPreparing = false
          }
        }, this)
      }, 300)
    })
  },

  /* 分享缩略图 · 紧凑版融合解读（最多 2 行） */
  _pInsightCompact(ctx, w, y, C) {
    const summary = String((this.submitData && this.submitData.free_summary) || '').replace(/\n/g, ' ').trim()
    if (!summary) return y
    const mx = 40
    const maxW = w - mx * 2 - 40
    ctx.font = '14px sans-serif'
    const allLines = this._wrapText(ctx, summary, maxW)
    const lines = allLines.slice(0, 2)
    if (allLines.length > 2) {
      let last = lines[lines.length - 1] || ''
      while (last.length > 0 && ctx.measureText(last + '…').width > maxW) { last = last.slice(0, -1) }
      lines[lines.length - 1] = last + '…'
    }
    const cardH = 28 + lines.length * 22 + 12

    this._drawRoundRect(ctx, mx, y, w - mx * 2, cardH, 12)
    ctx.setFillStyle('rgba(255,249,244,0.92)')
    ctx.fill()
    ctx.setStrokeStyle('rgba(242,84,91,0.16)')
    ctx.setLineWidth(1)
    ctx.stroke()

    ctx.setTextAlign('left')
    ctx.setFillStyle(C.textSub)
    ctx.font = '14px sans-serif'
    lines.forEach((line, i) => {
      ctx.fillText(line, mx + 20, y + 26 + i * 22)
    })
    return y + cardH + 16
  },

  /* ============================================================
     生成分享海报（免费版卡片海报，600×1080）
     ============================================================ */
  onPoster() {
    if (this._posting) return
    this._posting = true
    wx.showLoading({ title: '正在生成海报...', mask: true })

    const w = 600
    const h = 1080
    const ctx = wx.createCanvasContext('posterCanvas', this)
    const C = POSTER_COLORS

    // 背景：暖色纵向渐变
    const grad = ctx.createLinearGradient(0, 0, 0, h)
    grad.addColorStop(0, '#FFF6EC')
    grad.addColorStop(0.35, '#FDF8F3')
    grad.addColorStop(1, '#F6F1FA')
    ctx.setFillStyle(grad)
    ctx.fillRect(0, 0, w, h)

    // 定点星光
    POSTER_STARS.forEach((s) => {
      ctx.beginPath()
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
      ctx.setFillStyle(`rgba(${s.c},${s.a})`)
      ctx.fill()
    })

    let y = 58
    y = this._pBrand(ctx, w, y, C)
    y = this._pGreeting(ctx, w, y, C)
    y = this._pSystemGrid(ctx, w, y, C)
    y = this._pInsight(ctx, w, y, C)
    y = this._pMbtiBars(ctx, w, y, C)
    y = this._pHollandTop(ctx, w, y, C)
    this._pFooter(ctx, w, h, C)

    ctx.draw(false, () => {
      setTimeout(() => {
        wx.canvasToTempFilePath({
          canvasId: 'posterCanvas',
          success: (res) => {
            this._savePoster(res.tempFilePath)
          },
          fail: () => {
            wx.hideLoading()
            this._posting = false
            wx.showToast({ title: '海报生成失败，请重试', icon: 'none' })
          }
        }, this)
      }, 300)
    })
  },

  _savePoster(filePath) {
    wx.saveImageToPhotosAlbum({
      filePath,
      success: () => {
        wx.hideLoading()
        this._posting = false
        wx.showToast({ title: '海报已保存到相册', icon: 'success' })
      },
      fail: (err) => {
        wx.hideLoading()
        this._posting = false
        const msg = (err && err.errMsg) || ''
        if (msg.indexOf('auth') > -1 || msg.indexOf('deny') > -1) {
          wx.showModal({
            title: '需要相册权限',
            content: '保存海报需要访问你的相册，请在设置中开启权限',
            confirmText: '去设置',
            success: (res) => { if (res.confirm) wx.openSetting() }
          })
        } else {
          wx.showToast({ title: '保存失败，请重试', icon: 'none' })
        }
      }
    })
  },

  /* ---- 海报 · 品牌区 ---- */
  _pBrand(ctx, w, y, C) {
    const brand = '星鉴人格'
    ctx.font = 'bold 32px sans-serif'
    const tw = ctx.measureText(brand).width
    const logoSize = 38
    const gap = 11
    const startX = (w - logoSize - gap - tw) / 2

    ctx.drawImage('/assets/logo.png', startX, y - 14, logoSize, logoSize)
    ctx.setTextAlign('left')
    ctx.setTextBaseline('alphabetic')
    ctx.setFillStyle(C.textMain)
    ctx.font = 'bold 32px sans-serif'
    ctx.fillText(brand, startX + logoSize + gap, y + 17)
    ctx.setTextAlign('center')

    ctx.setFillStyle(C.textMuted)
    ctx.font = '13px sans-serif'
    ctx.fillText('人格深度测评报告', w / 2, y + 42)

    ctx.beginPath()
    ctx.moveTo(w / 2 - 50, y + 60)
    ctx.lineTo(w / 2 + 50, y + 60)
    ctx.setStrokeStyle('rgba(242,84,91,0.30)')
    ctx.setLineWidth(2)
    ctx.stroke()

    return y + 84
  },

  /* ---- 海报 · 用户标题 ---- */
  _pGreeting(ctx, w, y, C) {
    const profile = storage.getProfile() || {}
    const name = profile.name || '你'
    ctx.setTextAlign('center')
    ctx.setFillStyle(C.textMain)
    ctx.font = 'bold 28px sans-serif'
    ctx.fillText(`${name}的人格画像`, w / 2, y + 20)
    return y + 44
  },

  /* ---- 海报 · 四体系总览（2×2 并列卡） ---- */
  _pSystemGrid(ctx, w, y, C) {
    const r = this.results || {}
    const cards = []
    if (r.mbti) cards.push({ title: '人格类型', type: r.mbti.type || '', color: '#3B9ED8' })
    if (r.enneagram) {
      const num = r.enneagram.main_type
      const nm = r.enneagram.type_name || labels.ENNEAGRAM_NAMES[num] || ''
      cards.push({ title: '九型人格', type: `${num}号·${nm}`, color: '#F2545B' })
    }
    if (r.holland) cards.push({ title: '职业兴趣', type: r.holland.code || '', color: '#F59E0B' })
    if (r.gallup) cards.push({ title: '优势领域', type: labels.GALLUP_DOMAINS[r.gallup.top_domain] || r.gallup.top_domain, color: '#8B5CF6' })
    if (!cards.length) return y

    const mx = 40, gap = 12, cw = (w - mx * 2 - gap) / 2, ch = 92
    cards.slice(0, 4).forEach((c, i) => {
      const col = i % 2, row = Math.floor(i / 2)
      const cx = mx + col * (cw + gap), cy = y + row * (ch + gap)
      this._drawRoundRect(ctx, cx, cy, cw, ch, 12)
      ctx.setFillStyle(C.cardBg); ctx.fill()
      this._drawRoundRect(ctx, cx, cy, cw, 4, 2)
      ctx.setFillStyle(c.color); ctx.fill()
      ctx.setTextAlign('left'); ctx.setFillStyle(C.textMuted); ctx.font = '12px sans-serif'
      ctx.fillText(c.title, cx + 16, cy + 30)
      ctx.setFillStyle(c.color); ctx.font = 'bold 19px sans-serif'
      ctx.fillText(this._truncateText(ctx, c.type, cw - 32), cx + 16, cy + 62)
    })
    const rows = Math.ceil(Math.min(cards.length, 4) / 2)
    return y + rows * ch + (rows - 1) * gap + 20
  },

  /* ---- 海报 · 融合解读 ---- */
  _pInsight(ctx, w, y, C) {
    const summary = String((this.submitData && this.submitData.free_summary) || '').replace(/\n/g, ' ').trim()
    if (!summary) return y
    const mx = 40, maxW = w - mx * 2 - 56
    ctx.font = '15px sans-serif'
    const allLines = this._wrapText(ctx, summary, maxW)
    const lines = allLines.slice(0, 4)
    if (allLines.length > 4) {
      let last = lines[lines.length - 1] || ''
      while (last.length > 0 && ctx.measureText(last + '…').width > maxW) { last = last.slice(0, -1) }
      lines[lines.length - 1] = last + '…'
    }
    const cardH = 44 + lines.length * 24 + 16

    this._drawRoundRect(ctx, mx, y, w - mx * 2, cardH, 16)
    ctx.setFillStyle('rgba(255,249,244,0.92)'); ctx.fill()
    ctx.setStrokeStyle('rgba(242,84,91,0.16)'); ctx.setLineWidth(1); ctx.stroke()

    ctx.setTextAlign('left'); ctx.setFillStyle('rgba(242,84,91,0.35)'); ctx.font = 'bold 36px serif'
    ctx.fillText('\u201C', mx + 18, y + 38)

    ctx.setFillStyle(C.textSub); ctx.font = '15px sans-serif'
    lines.forEach((line, i) => ctx.fillText(line, mx + 30, y + 46 + i * 24))
    return y + cardH + 20
  },

  /* ---- 海报 · MBTI 维度条 ---- */
  _pMbtiBars(ctx, w, y, C) {
    const mbti = (this.results || {}).mbti
    if (!mbti || !mbti.dimensions) return y
    const d = mbti.dimensions
    const pairs = [
      { left: 'E', right: 'I', lv: d.E || 0, rv: d.I || 0, ll: '外向', rl: '内向' },
      { left: 'S', right: 'N', lv: d.S || 0, rv: d.N || 0, ll: '实感', rl: '直觉' },
      { left: 'T', right: 'F', lv: d.T || 0, rv: d.F || 0, ll: '思考', rl: '情感' },
      { left: 'J', right: 'P', lv: d.J || 0, rv: d.P || 0, ll: '判断', rl: '感知' },
    ]
    const bars = pairs.map(p => {
      const total = p.lv + p.rv || 1
      return { ...p, lp: Math.round((p.lv / total) * 100), rp: 100 - Math.round((p.lv / total) * 100), dom: p.lv >= p.rv ? p.left : p.right }
    })

    const mx = 40
    ctx.setFillStyle(C.coral); ctx.fillRect(mx, y + 2, 4, 16)
    ctx.setTextAlign('left'); ctx.setFillStyle(C.textMain); ctx.font = 'bold 17px sans-serif'
    ctx.fillText('MBTI 认知维度', mx + 12, y + 16)

    const barX = mx + 96, barW = w - mx * 2 - 96 * 2, barH = 12
    let by = y + 36
    bars.forEach((b) => {
      const cy = by + barH / 2 + 5
      ctx.setTextAlign('left')
      ctx.setFillStyle(b.left === b.dom ? C.blue : C.textMuted); ctx.font = 'bold 15px sans-serif'
      ctx.fillText(b.left, mx, cy)
      ctx.setFillStyle(C.textMuted); ctx.font = '12px sans-serif'
      ctx.fillText(b.ll, mx + 22, cy)

      this._drawRoundRect(ctx, barX, by, barW, barH, 6)
      ctx.setFillStyle(C.trackBg); ctx.fill()
      if (b.lp > 0) {
        const lw = Math.max((barW * b.lp) / 100, barH)
        if (b.lp >= 100) { this._drawRoundRect(ctx, barX, by, lw, barH, 6) } else { this._barHalf(ctx, barX, by, lw, barH, 6, 'left') }
        ctx.setFillStyle(C.blue); ctx.fill()
      }
      if (b.rp > 0) {
        const rw = Math.max((barW * b.rp) / 100, barH)
        if (b.rp >= 100) { this._drawRoundRect(ctx, barX + barW - rw, by, rw, barH, 6) } else { this._barHalf(ctx, barX + barW - rw, by, rw, barH, 6, 'right') }
        ctx.setFillStyle(C.coral); ctx.fill()
      }

      ctx.setTextAlign('right')
      ctx.setFillStyle(b.right === b.dom ? C.coral : C.textMuted); ctx.font = 'bold 15px sans-serif'
      ctx.fillText(b.right, w - mx, cy)
      ctx.setFillStyle(C.textMuted); ctx.font = '12px sans-serif'
      ctx.fillText(b.rl, w - mx - 24, cy)
      by += 34
    })
    return by + 8
  },

  /* ---- 海报 · 霍兰德 Top 3 ---- */
  _pHollandTop(ctx, w, y, C) {
    const holland = (this.results || {}).holland
    if (!holland || !holland.scores) return y
    const names = labels.HOLLAND_NAMES
    const s = holland.scores
    const max = Math.max(...Object.values(s), 1)
    const items = [
      { code: 'S', name: names.S, score: s.S || 0 },
      { code: 'A', name: names.A, score: s.A || 0 },
      { code: 'E', name: names.E, score: s.E || 0 },
      { code: 'C', name: names.C, score: s.C || 0 },
      { code: 'I', name: names.I, score: s.I || 0 },
      { code: 'R', name: names.R, score: s.R || 0 },
    ]
    items.sort((a, b) => b.score - a.score)
    const bars = items.slice(0, 3).map(it => ({ ...it, pct: Math.round((it.score / max) * 100) }))

    const mx = 40
    ctx.setFillStyle(C.orange); ctx.fillRect(mx, y + 2, 4, 16)
    ctx.setTextAlign('left'); ctx.setFillStyle(C.textMain); ctx.font = 'bold 17px sans-serif'
    ctx.fillText('霍兰德职业兴趣 Top 3', mx + 12, y + 16)

    const barX = mx + 96, scoreW = 40, barW = w - mx * 2 - 96 - scoreW - 16, barH = 10
    let by = y + 38
    bars.forEach((b) => {
      const cy = by + barH / 2 + 4
      ctx.setTextAlign('left')
      ctx.setFillStyle(C.orange); ctx.font = 'bold 15px sans-serif'
      ctx.fillText(b.code, mx, cy)
      ctx.setFillStyle(C.textMuted); ctx.font = '12px sans-serif'
      ctx.fillText(b.name, mx + 24, cy)

      this._drawRoundRect(ctx, barX, by, barW, barH, 5)
      ctx.setFillStyle(C.trackBg); ctx.fill()
      const fw = Math.max((barW * b.pct) / 100, barH)
      this._drawRoundRect(ctx, barX, by, fw, barH, 5)
      ctx.setFillStyle(C.orange); ctx.fill()

      ctx.setTextAlign('right'); ctx.setFillStyle(C.textMain); ctx.font = 'bold 14px sans-serif'
      ctx.fillText(String(b.score), w - mx, cy)
      by += 30
    })
    return by + 8
  },

  /* ---- 海报 · 页脚（小程序码 + Slogan） ---- */
  _pFooter(ctx, w, h, C) {
    const qrSize = 96, qrX = 48, qrY = h - 40 - qrSize
    this._drawRoundRect(ctx, qrX - 8, qrY - 8, qrSize + 16, qrSize + 16, 16)
    ctx.setFillStyle('#FFFFFF'); ctx.fill()
    ctx.setStrokeStyle('rgba(139,92,246,0.18)'); ctx.setLineWidth(1); ctx.stroke()
    ctx.drawImage('/assets/miniprogram-code.jpg', qrX, qrY, qrSize, qrSize)

    const tx = qrX + qrSize + 28
    ctx.setTextAlign('left'); ctx.setFillStyle(C.textSub); ctx.font = '14px sans-serif'
    ctx.fillText('长按扫码，开启你的人格探索', tx, qrY + 26)
    ctx.setFillStyle(C.coralDeep); ctx.font = 'bold 24px sans-serif'
    ctx.fillText('发现你的独特光芒', tx, qrY + 58)
    ctx.setFillStyle(C.textMuted); ctx.font = '12px sans-serif'
    ctx.fillText('星鉴人格 · 星耀启程出品', tx, qrY + 82)
  },

  /* ---- 海报工具函数 ---- */
  _drawRoundRect(ctx, x, y, w, h, r) {
    ctx.beginPath()
    ctx.moveTo(x + r, y)
    ctx.arcTo(x + w, y, x + w, y + h, r)
    ctx.arcTo(x + w, y + h, x, y + h, r)
    ctx.arcTo(x, y + h, x, y, r)
    ctx.arcTo(x, y, x + w, y, r)
    ctx.closePath()
  },

  _barHalf(ctx, x, y, w, h, r, side) {
    const rr = Math.min(r, w / 2, h / 2)
    ctx.beginPath()
    if (side === 'left') {
      ctx.moveTo(x + w, y); ctx.lineTo(x + rr, y); ctx.arcTo(x, y, x, y + rr, rr)
      ctx.lineTo(x, y + h - rr); ctx.arcTo(x, y + h, x + rr, y + h, rr); ctx.lineTo(x + w, y + h)
    } else {
      ctx.moveTo(x, y); ctx.lineTo(x + w - rr, y); ctx.arcTo(x + w, y, x + w, y + rr, rr)
      ctx.lineTo(x + w, y + h - rr); ctx.arcTo(x + w, y + h, x + w - rr, y + h, rr); ctx.lineTo(x, y + h)
    }
    ctx.closePath()
  },

  _wrapText(ctx, text, maxWidth) {
    const lines = []
    let line = ''
    for (const ch of String(text)) {
      if (ch === '\n') { lines.push(line); line = ''; continue }
      if (line && ctx.measureText(line + ch).width > maxWidth) { lines.push(line); line = ch } else { line += ch }
    }
    if (line) lines.push(line)
    return lines
  },

  _truncateText(ctx, text, maxWidth) {
    if (!text) return ''
    if (ctx.measureText(text).width <= maxWidth) return text
    let t = String(text)
    while (t.length > 0 && ctx.measureText(t + '…').width > maxWidth) { t = t.slice(0, -1) }
    return t + '…'
  },

  onShareAppMessage() {
    const share = {
      title: '测一测你的人格画像，发现你的独特光芒',
      path: '/pages/index/index'
    }
    // 优先使用预生成的四卡片海报作为分享图
    if (this.data.shareImagePath) {
      share.imageUrl = this.data.shareImagePath
    }
    return share
  }
})
