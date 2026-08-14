/**
 * pages/result-full/result-full.js — 完整深度报告页
 *
 * - 调 /api/report/detail 获取完整报告；返回 code=2001（生成中）则持续轮询
 * - 用 utils/markdown.js 渲染六大章节 markdown
 * - 底部操作栏：生成分享海报 / 转发好友 / 保存报告
 */
const api = require('../../utils/api')
const config = require('../../utils/config')
const storage = require('../../utils/storage')
const labels = require('../../utils/labels')
const markdown = require('../../utils/markdown')

// 海报配色（与设计 token 对齐；Canvas 无法读取 CSS 变量，修改 token 时需同步此处）
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

// 海报星光（固定坐标，保证每次生成结果一致；仅点缀顶部区域，透明度克制）
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

// 章节图标映射
const SECTION_ICONS = {
  '人格': '🎭', '类型': '🎭', '画像': '🎭', '特质': '🎭',
  '优势': '💎', '天赋': '💎', '潜能': '💎', '力量': '💎',
  '职业': '🧭', '发展': '🧭', '方向': '🧭', '事业': '🧭',
  '关系': '🤝', '人际': '🤝', '社交': '🤝', '团队': '🤝',
  '成长': '🌱', '建议': '🌱', '行动': '🌱', '提升': '🌱',
  '挑战': '⚡', '风险': '⚡', '盲区': '⚡', '弱点': '⚡',
  '协同': '🔗', '融合': '🔗', '交叉': '🔗', '整合': '🔗',
  '总结': '✨', '结语': '✨', '未来': '✨', '展望': '✨',
}

function pickIcon(title) {
  for (const key in SECTION_ICONS) {
    if (title && title.includes(key)) return SECTION_ICONS[key]
  }
  return '📖'
}

Page({
  data: {
    loading: true,
    greet: '',
    typeBadges: [],
    generatedAt: '',
    sections: [],
    // 可视化数据
    snapshotCards: [],   // 四体系快照卡片
    mbtiBars: [],        // MBTI 维度进度条
    hollandBars: [],     // 霍兰德六型条形图
    gallupBars: [],      // 盖洛普四领域条形图
    hasResults: false,   // 是否有可视化数据
    hasIncomplete: false, // 是否有章节内容不完整
    canRegenerate: true, // 是否还能重新生成
    regenerating: false, // 正在重新生成
    posterW: 600,
    posterH: 1080,
    shareImagePath: '',  // 预生成的海报本地路径，用于转发 imageUrl
  },

  onLoad(options) {
    const results = storage.getResults() || {}
    const sessionId = (options && options.session_id) || results.session_id || ''
    if (!sessionId) {
      wx.showToast({ title: '会话不存在，请重新测评', icon: 'none' })
      setTimeout(() => wx.redirectTo({ url: '/pages/result-free/result-free' }), 1200)
      return
    }
    this.sessionId = sessionId
    this.posting = false

    // 已缓存的完整报告直接渲染
    const cached = storage.getReport()
    if (cached && cached.sections && cached.sections.length) {
      this.renderReport(cached)
      return
    }
    this.fetchReport()
  },

  onUnload() {
    this.stopPolling()
  },

  /* ============================================================
     获取报告（2001 生成中 → 轮询）
     ============================================================ */
  fetchReport() {
    api
      .getReportDetail(this.sessionId)
      .then((data) => {
        const report = (data && data.report) || data || {}
        if (!report.sections || !report.sections.length) {
          this.schedulePoll()
          return
        }
        this.stopPolling()
        this.renderReport(report)
        storage.setReport(report)
      })
      .catch((err) => {
        // 报告生成中（2001）→ 继续轮询
        if (err && err.code === api.ERR.REPORT_GENERATING) {
          this.schedulePoll()
          return
        }
        this.setData({ loading: false })
        wx.showToast({ title: (err && err.message) || '报告获取失败，请重试', icon: 'none' })
      })
  },

  schedulePoll() {
    if (this.pollTimer) return
    this.pollTimer = setTimeout(() => {
      this.pollTimer = null
      this.fetchReport()
    }, config.POLL_INTERVAL_MS)
  },

  stopPolling() {
    if (this.pollTimer) {
      clearTimeout(this.pollTimer)
      this.pollTimer = null
    }
  },

  /* ============================================================
     渲染报告
     ============================================================ */
  renderReport(report) {
    const r = report.results || {}

    // 章节渲染（加图标）
    const sections = (report.sections || []).map((s, i) => ({
      index: String(i + 1).padStart(2, '0'),
      title: s.title || `章节 ${i + 1}`,
      icon: pickIcon(s.title),
      html: markdown.render(s.content),
      incomplete: !!s.incomplete
    }))

    // 检测是否有不完整章节
    const hasIncomplete = sections.some(s => s.incomplete)
    const canRegenerate = report.can_regenerate !== false && hasIncomplete

    // 类型标签
    const badges = []
    if (r.enneagram) {
      badges.push(`${r.enneagram.main_type}号 ${r.enneagram.type_name || labels.ENNEAGRAM_NAMES[r.enneagram.main_type] || ''}`)
    }
    if (r.mbti) badges.push(r.mbti.type)
    if (r.holland) badges.push(r.holland.code)
    if (r.gallup) {
      badges.push(labels.GALLUP_DOMAINS[r.gallup.top_domain] || r.gallup.top_domain)
    }

    const profile = report.profile || storage.getProfile() || {}
    const name = profile.name || '你'

    // 四体系快照卡片
    const snapshotCards = this._buildSnapshotCards(r)

    // MBTI 维度进度条
    const mbtiBars = this._buildMbtiBars(r.mbti)

    // 霍兰德条形图
    const hollandBars = this._buildHollandBars(r.holland)

    // 盖洛普条形图
    const gallupBars = this._buildGallupBars(r.gallup)

    this.setData({
      loading: false,
      greet: `你好，${name}！这是你的完整人格画像`,
      typeBadges: badges.filter(Boolean),
      generatedAt: report.generated_at || '',
      sections,
      snapshotCards,
      mbtiBars,
      hollandBars,
      gallupBars,
      hasResults: snapshotCards.length > 0,
      hasIncomplete,
      canRegenerate
    })

    // 报告就绪后静默预生成海报，用于分享时的 imageUrl（避免白色空白截图）
    this._preGenerateSharePoster()
  },

  /**
   * 静默预生成分享海报（不弹 loading、不保存到相册）
   * 失败时静默忽略：分享时 WeChat 会自动用页面截图兜底
   */
  _preGenerateSharePoster() {
    if (this._posterPreparing) return
    this._posterPreparing = true
    const w = 600
    const h = 1080
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
            this.setData({ shareImagePath: res.tempFilePath })
          },
          complete: () => {
            this._posterPreparing = false
          }
        }, this)
      }, 300)
    })
  },

  /* ---- 四体系快照卡片 ---- */
  _buildSnapshotCards(r) {
    const cards = []

    if (r.mbti) {
      const type = r.mbti.type || ''
      cards.push({
        key: 'mbti',
        icon: '🧩',
        title: '人格类型',
        type: type,
        desc: labels.MBTI_DESC[type] || '独特的人格类型',
        color: '#3B9ED8'
      })
    }

    if (r.enneagram) {
      const num = r.enneagram.main_type
      const name = r.enneagram.type_name || labels.ENNEAGRAM_NAMES[num] || ''
      cards.push({
        key: 'enneagram',
        icon: '🔢',
        title: '九型人格',
        type: `${num}号 ${name}`,
        desc: labels.ENNEAGRAM_DESC[num] || '',
        color: '#F2545B'
      })
    }

    if (r.holland) {
      const code = r.holland.code || ''
      const top = code.charAt(0)
      cards.push({
        key: 'holland',
        icon: '🎯',
        title: '职业兴趣',
        type: code,
        desc: labels.HOLLAND_DESC[top] || '',
        color: '#F59E0B'
      })
    }

    if (r.gallup) {
      const domain = r.gallup.top_domain || ''
      cards.push({
        key: 'gallup',
        icon: '💪',
        title: '优势领域',
        type: labels.GALLUP_DOMAINS[domain] || domain,
        desc: labels.GALLUP_DOMAIN_DESC[domain] || '',
        color: '#8B5CF6'
      })
    }

    return cards
  },

  /* ---- MBTI 维度进度条 ---- */
  _buildMbtiBars(mbti) {
    if (!mbti || !mbti.dimensions) return []
    const d = mbti.dimensions
    const pairs = [
      { left: 'E', right: 'I', leftVal: d.E || 0, rightVal: d.I || 0, leftLabel: '外向', rightLabel: '内向' },
      { left: 'S', right: 'N', leftVal: d.S || 0, rightVal: d.N || 0, leftLabel: '实感', rightLabel: '直觉' },
      { left: 'T', right: 'F', leftVal: d.T || 0, rightVal: d.F || 0, leftLabel: '思考', rightLabel: '情感' },
      { left: 'J', right: 'P', leftVal: d.J || 0, rightVal: d.P || 0, leftLabel: '判断', rightLabel: '感知' },
    ]
    return pairs.map(p => {
      const total = p.leftVal + p.rightVal || 1
      const leftPct = Math.round((p.leftVal / total) * 100)
      const rightPct = 100 - leftPct
      const dominant = p.leftVal >= p.rightVal ? p.left : p.right
      return { ...p, leftPct, rightPct, dominant }
    })
  },

  /* ---- 霍兰德六型条形图 ---- */
  _buildHollandBars(holland) {
    if (!holland || !holland.scores) return []
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
    // 按分数降序
    items.sort((a, b) => b.score - a.score)
    return items.map(item => ({
      ...item,
      pct: Math.round((item.score / max) * 100)
    }))
  },

  /* ---- 盖洛普四领域条形图 ---- */
  _buildGallupBars(gallup) {
    if (!gallup || !gallup.domains) return []
    const names = labels.GALLUP_DOMAINS
    const d = gallup.domains
    const max = Math.max(...Object.values(d), 1)
    const items = [
      { key: 'relationship_building', name: names.relationship_building, score: d.relationship_building || 0, color: '#F2545B' },
      { key: 'strategic_thinking', name: names.strategic_thinking, score: d.strategic_thinking || 0, color: '#3B9ED8' },
      { key: 'executing', name: names.executing, score: d.executing || 0, color: '#F59E0B' },
      { key: 'influencing', name: names.influencing, score: d.influencing || 0, color: '#8B5CF6' },
    ]
    items.sort((a, b) => b.score - a.score)
    return items.map(item => ({
      ...item,
      pct: Math.round((item.score / max) * 100)
    }))
  },

  /* ============================================================
     生成分享海报 —— 版式 v4（四体系均衡版）
     设计原则：四体系并列无主角 + 一两句融合解读 + 确定性装饰 + 无 emoji（Canvas 渲染不稳定）
     画布 600x1080，纵向流式分区（各方法返回下一区起始 y），页脚锚定底部
     ============================================================ */
  onPoster() {
    if (this.posting) return
    this.posting = true
    wx.showLoading({ title: '正在生成海报...', mask: true })

    const w = 600
    const h = 1080
    const ctx = wx.createCanvasContext('posterCanvas', this)
    const C = POSTER_COLORS

    // ---- 背景：暖色纵向渐变 ----
    const grad = ctx.createLinearGradient(0, 0, 0, h)
    grad.addColorStop(0, '#FFF6EC')
    grad.addColorStop(0.35, '#FDF8F3')
    grad.addColorStop(1, '#F6F1FA')
    ctx.setFillStyle(grad)
    ctx.fillRect(0, 0, w, h)

    // ---- 定点星光（固定坐标，每次生成一致） ----
    POSTER_STARS.forEach((s) => {
      ctx.beginPath()
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
      ctx.setFillStyle(`rgba(${s.c},${s.a})`)
      ctx.fill()
    })

    // ---- 分区绘制 ----
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
            this.savePoster(res.tempFilePath)
          },
          fail: () => {
            wx.hideLoading()
            this.posting = false
            wx.showToast({ title: '海报生成失败，请重试', icon: 'none' })
          }
        }, this)
      }, 300)
    })
  },

  /* ---- 海报 · 品牌区 ---- */
  _pBrand(ctx, w, y, C) {
    // 顶部装饰双环
    ctx.beginPath()
    ctx.arc(w / 2, y + 6, 30, 0, Math.PI * 2)
    ctx.setFillStyle('rgba(242,84,91,0.07)')
    ctx.fill()
    ctx.beginPath()
    ctx.arc(w / 2, y + 6, 20, 0, Math.PI * 2)
    ctx.setFillStyle('rgba(139,92,246,0.10)')
    ctx.fill()

    ctx.setTextAlign('center')
    ctx.setFillStyle(C.textMain)
    ctx.font = 'bold 30px sans-serif'
    ctx.fillText('星鉴人格', w / 2, y + 16)

    ctx.setFillStyle(C.textMuted)
    ctx.font = '15px sans-serif'
    ctx.fillText('人格深度测评报告', w / 2, y + 42)

    // 分隔线
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
    ctx.font = 'bold 26px sans-serif'
    ctx.fillText(`${name}的人格画像`, w / 2, y + 20)
    return y + 44
  },

  /* ---- 海报 · 四体系总览（2×2 并列卡，无主角，各自体系色） ---- */
  _pSystemGrid(ctx, w, y, C) {
    const cards = (this.data.snapshotCards || []).slice(0, 4)
    if (!cards.length) return y

    const mx = 40
    const gap = 12
    const cw = (w - mx * 2 - gap) / 2
    const ch = 92

    cards.forEach((c, i) => {
      const col = i % 2
      const row = Math.floor(i / 2)
      const cx = mx + col * (cw + gap)
      const cy = y + row * (ch + gap)

      // 卡底
      this._drawRoundRect(ctx, cx, cy, cw, ch, 12)
      ctx.setFillStyle(C.cardBg)
      ctx.fill()
      // 顶部色条（体系色）
      this._drawRoundRect(ctx, cx, cy, cw, 4, 2)
      ctx.setFillStyle(c.color)
      ctx.fill()
      // 体系名
      ctx.setTextAlign('left')
      ctx.setFillStyle(C.textMuted)
      ctx.font = '12px sans-serif'
      ctx.fillText(c.title, cx + 16, cy + 30)
      // 类型值（体系色大字）
      ctx.setFillStyle(c.color)
      ctx.font = 'bold 20px sans-serif'
      ctx.fillText(c.type, cx + 16, cy + 62)
    })

    const rows = Math.ceil(cards.length / 2)
    return y + rows * ch + (rows - 1) * gap + 20
  },

  /* ---- 海报 · 融合解读（一两句人话总结，永不为空） ---- */
  _pInsight(ctx, w, y, C) {
    const insight = this._buildInsight()
    if (!insight) return y

    const mx = 40
    ctx.font = '15px sans-serif'
    const lines = this._wrapText(ctx, insight, w - mx * 2 - 56).slice(0, 3)
    const cardH = 44 + lines.length * 24 + 16

    // 柔和卡片底 + 浅珊瑚描边
    this._drawRoundRect(ctx, mx, y, w - mx * 2, cardH, 16)
    ctx.setFillStyle('rgba(255,249,244,0.92)')
    ctx.fill()
    ctx.setStrokeStyle('rgba(242,84,91,0.16)')
    ctx.setLineWidth(1)
    ctx.stroke()

    // 引号装饰
    ctx.setTextAlign('left')
    ctx.setFillStyle('rgba(242,84,91,0.35)')
    ctx.font = 'bold 36px serif'
    ctx.fillText('“', mx + 18, y + 38)

    ctx.setFillStyle(C.textSub)
    ctx.font = '15px sans-serif'
    lines.forEach((line, i) => {
      ctx.fillText(line, mx + 30, y + 46 + i * 24)
    })

    return y + cardH + 20
  },

  /* 融合解读文案：优先 AI 生成的免费简述；缺失时用各体系描述拼接兜底 */
  _buildInsight() {
    const results = storage.getResults() || {}
    const summary = String(results.free_summary || '').replace(/\n/g, ' ').trim()
    if (summary) return summary
    const descs = (this.data.snapshotCards || []).map((c) => c.desc).filter(Boolean)
    if (descs.length >= 2) return descs.slice(0, 2).join('；') + '。'
    if (descs.length === 1) return descs[0]
    return ''
  },

  /* ---- 海报 · MBTI 维度条（左右对比，相接端直角无缝） ---- */
  _pMbtiBars(ctx, w, y, C) {
    const bars = this.data.mbtiBars
    if (!bars.length) return y

    const mx = 40
    // 小节标题（竖条 + 文字）
    ctx.setFillStyle(C.coral)
    ctx.fillRect(mx, y + 2, 4, 16)
    ctx.setTextAlign('left')
    ctx.setFillStyle(C.textMain)
    ctx.font = 'bold 17px sans-serif'
    ctx.fillText('MBTI 认知维度', mx + 12, y + 16)

    const barX = mx + 96
    const barW = w - mx * 2 - 96 * 2
    const barH = 12
    let by = y + 36

    bars.forEach((b) => {
      const cy = by + barH / 2 + 5
      // 左标签
      ctx.setTextAlign('left')
      ctx.setFillStyle(b.left === b.dominant ? C.blue : C.textMuted)
      ctx.font = 'bold 15px sans-serif'
      ctx.fillText(b.left, mx, cy)
      ctx.setFillStyle(C.textMuted)
      ctx.font = '12px sans-serif'
      ctx.fillText(b.leftLabel, mx + 22, cy)

      // 轨道
      this._drawRoundRect(ctx, barX, by, barW, barH, 6)
      ctx.setFillStyle(C.trackBg)
      ctx.fill()
      // 左填充（蓝）：右端直角与右填充无缝相接；100% 时退化为全圆角
      if (b.leftPct > 0) {
        const lw = Math.max((barW * b.leftPct) / 100, barH)
        if (b.leftPct >= 100) {
          this._drawRoundRect(ctx, barX, by, lw, barH, 6)
        } else {
          this._barHalf(ctx, barX, by, lw, barH, 6, 'left')
        }
        ctx.setFillStyle(C.blue)
        ctx.fill()
      }
      // 右填充（珊瑚）：左端直角
      if (b.rightPct > 0) {
        const rw = Math.max((barW * b.rightPct) / 100, barH)
        if (b.rightPct >= 100) {
          this._drawRoundRect(ctx, barX + barW - rw, by, rw, barH, 6)
        } else {
          this._barHalf(ctx, barX + barW - rw, by, rw, barH, 6, 'right')
        }
        ctx.setFillStyle(C.coral)
        ctx.fill()
      }

      // 右标签
      ctx.setTextAlign('right')
      ctx.setFillStyle(b.right === b.dominant ? C.coral : C.textMuted)
      ctx.font = 'bold 15px sans-serif'
      ctx.fillText(b.right, w - mx, cy)
      ctx.setFillStyle(C.textMuted)
      ctx.font = '12px sans-serif'
      ctx.fillText(b.rightLabel, w - mx - 24, cy)

      by += 34
    })

    return by + 8
  },

  /* ---- 海报 · 霍兰德 Top 3（单值横条，橙色） ---- */
  _pHollandTop(ctx, w, y, C) {
    const bars = (this.data.hollandBars || []).slice(0, 3)
    if (!bars.length) return y

    const mx = 40
    // 小节标题
    ctx.setFillStyle(C.orange)
    ctx.fillRect(mx, y + 2, 4, 16)
    ctx.setTextAlign('left')
    ctx.setFillStyle(C.textMain)
    ctx.font = 'bold 17px sans-serif'
    ctx.fillText('霍兰德职业兴趣 Top 3', mx + 12, y + 16)

    const barX = mx + 96
    const scoreW = 40
    const barW = w - mx * 2 - 96 - scoreW - 16
    const barH = 10
    let by = y + 38

    bars.forEach((b) => {
      const cy = by + barH / 2 + 4
      // 左标签
      ctx.setTextAlign('left')
      ctx.setFillStyle(C.orange)
      ctx.font = 'bold 15px sans-serif'
      ctx.fillText(b.code, mx, cy)
      ctx.setFillStyle(C.textMuted)
      ctx.font = '12px sans-serif'
      ctx.fillText(b.name, mx + 24, cy)

      // 轨道 + 填充
      this._drawRoundRect(ctx, barX, by, barW, barH, 5)
      ctx.setFillStyle(C.trackBg)
      ctx.fill()
      const fw = Math.max((barW * b.pct) / 100, barH)
      this._drawRoundRect(ctx, barX, by, fw, barH, 5)
      ctx.setFillStyle(C.orange)
      ctx.fill()

      // 分数
      ctx.setTextAlign('right')
      ctx.setFillStyle(C.textMain)
      ctx.font = 'bold 14px sans-serif'
      ctx.fillText(String(b.score), w - mx, cy)

      by += 30
    })

    return by + 8
  },

  /* ---- 海报 · 页脚（小程序码 + Slogan，锚定底部） ---- */
  _pFooter(ctx, w, h, C) {
    const qrSize = 96
    const qrX = 48
    const qrY = h - 40 - qrSize

    // 小程序码图片
    ctx.drawImage('/assets/miniprogram-code.jpg', qrX, qrY, qrSize, qrSize)

    // 右侧文案块
    const tx = qrX + qrSize + 28
    ctx.setTextAlign('left')
    ctx.setFillStyle(C.textSub)
    ctx.font = '14px sans-serif'
    ctx.fillText('长按扫码，开启你的人格探索', tx, qrY + 26)

    ctx.setFillStyle(C.coralDeep)
    ctx.font = 'bold 24px sans-serif'
    ctx.fillText('发现你的独特光芒', tx, qrY + 58)

    ctx.setFillStyle(C.textMuted)
    ctx.font = '12px sans-serif'
    ctx.fillText('星鉴人格 · 星耀启程出品', tx, qrY + 82)
  },

  /* 海报工具 · 半圆角横条（side='left' 左端圆角右端直角；'right' 反之） */
  _barHalf(ctx, x, y, w, h, r, side) {
    const rr = Math.min(r, w / 2, h / 2)
    ctx.beginPath()
    if (side === 'left') {
      ctx.moveTo(x + w, y)
      ctx.lineTo(x + rr, y)
      ctx.arcTo(x, y, x, y + rr, rr)
      ctx.lineTo(x, y + h - rr)
      ctx.arcTo(x, y + h, x + rr, y + h, rr)
      ctx.lineTo(x + w, y + h)
    } else {
      ctx.moveTo(x, y)
      ctx.lineTo(x + w - rr, y)
      ctx.arcTo(x + w, y, x + w, y + rr, rr)
      ctx.lineTo(x + w, y + h - rr)
      ctx.arcTo(x + w, y + h, x + w - rr, y + h, rr)
      ctx.lineTo(x, y + h)
    }
    ctx.closePath()
  },

  /* 海报工具 · 文本自动换行（中英文按字符累计宽度；需先设置 ctx.font） */
  _wrapText(ctx, text, maxWidth) {
    const lines = []
    let line = ''
    for (const ch of String(text)) {
      if (ch === '\n') {
        lines.push(line)
        line = ''
        continue
      }
      if (line && ctx.measureText(line + ch).width > maxWidth) {
        lines.push(line)
        line = ch
      } else {
        line += ch
      }
    }
    if (line) lines.push(line)
    return lines
  },

  /* 绘制圆角矩形路径 */
  _drawRoundRect(ctx, x, y, w, h, r) {
    ctx.beginPath()
    ctx.moveTo(x + r, y)
    ctx.arcTo(x + w, y, x + w, y + h, r)
    ctx.arcTo(x + w, y + h, x, y + h, r)
    ctx.arcTo(x, y + h, x, y, r)
    ctx.arcTo(x, y, x + w, y, r)
    ctx.closePath()
  },

  savePoster(filePath) {
    wx.saveImageToPhotosAlbum({
      filePath,
      success: () => {
        wx.hideLoading()
        this.posting = false
        wx.showToast({ title: '海报已保存到相册', icon: 'success' })
      },
      fail: (err) => {
        wx.hideLoading()
        this.posting = false
        const msg = (err && err.errMsg) || ''
        if (msg.indexOf('auth') > -1 || msg.indexOf('deny') > -1) {
          wx.showModal({
            title: '需要相册权限',
            content: '保存海报需要访问你的相册，请在设置中开启权限',
            confirmText: '去设置',
            success: (res) => {
              if (res.confirm) wx.openSetting()
            }
          })
        } else {
          wx.showToast({ title: '保存失败，请重试', icon: 'none' })
        }
      }
    })
  },

  /* ============================================================
     重新生成报告（已付费，不重复收费）
     ============================================================ */
  onRegenerate() {
    if (this.data.regenerating) return
    this.setData({ regenerating: true })

    api
      .regenerateReport(this.sessionId)
      .then(() => {
        // 清除本地缓存的旧报告
        storage.setReport(null)
        // 重新轮询
        this.setData({ loading: true, regenerating: false })
        this.fetchReport()
      })
      .catch((err) => {
        this.setData({ regenerating: false })
        wx.showToast({ title: (err && err.message) || '重新生成失败，请重试', icon: 'none' })
      })
  },

  /* ============================================================
     保存报告（Markdown 文本写入本地）
     ============================================================ */
  onSaveReport() {
    const report = storage.getReport()
    if (!report || !report.sections || !report.sections.length) {
      wx.showToast({ title: '报告尚未生成完成', icon: 'none' })
      return
    }

    let md = '# 星鉴人格 · 完整人格深度报告\n\n'
    md += `生成时间：${report.generated_at || ''}\n\n---\n\n`
    report.sections.forEach((s) => {
      md += `${s.content}\n\n---\n\n`
    })

    const filePath = `${wx.env.USER_DATA_PATH}/星鉴人格测评报告.md`
    wx.getFileSystemManager().writeFile({
      filePath,
      data: md,
      encoding: 'utf8',
      success: () => {
        wx.showToast({ title: '报告已保存到本地', icon: 'success' })
      },
      fail: () => {
        wx.showToast({ title: '保存失败，请重试', icon: 'none' })
      }
    })
  },

  /* ============================================================
     转发
     ============================================================ */
  onShareAppMessage() {
    const share = {
      title: '我的人格画像已生成，一起来发现你的独特光芒',
      path: '/pages/index/index'
    }
    // 优先使用预生成的"四体系卡片海报"作为分享图（包含 2x2 卡片，无白底）
    if (this.data.shareImagePath) {
      share.imageUrl = this.data.shareImagePath
    }
    return share
  }
})
