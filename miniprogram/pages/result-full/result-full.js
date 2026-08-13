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
    posterH: 1080
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
        color: '#3B9DEA'
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
      { key: 'strategic_thinking', name: names.strategic_thinking, score: d.strategic_thinking || 0, color: '#3B9DEA' },
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
     生成分享海报（图表+解析+二维码预留位）
     ============================================================ */
  onPoster() {
    if (this.posting) return
    this.posting = true
    wx.showLoading({ title: '正在生成海报...', mask: true })

    const w = 600
    const h = 1080
    const ctx = wx.createCanvasContext('posterCanvas', this)

    // ---- 背景渐变 ----
    const grad = ctx.createLinearGradient(0, 0, 0, h)
    grad.addColorStop(0, '#FFF8F0')
    grad.addColorStop(0.3, '#FAF5FF')
    grad.addColorStop(0.7, '#F5F0FF')
    grad.addColorStop(1, '#F0F4FF')
    ctx.setFillStyle(grad)
    ctx.fillRect(0, 0, w, h)

    // ---- 星光点缀 ----
    const starColors = ['245,158,11', '139,92,246', '242,84,91', '59,158,216']
    for (let i = 0; i < 45; i++) {
      const x = Math.random() * w
      const y = Math.random() * h
      const r = Math.random() * 1.2 + 0.4
      ctx.beginPath()
      ctx.arc(x, y, r, 0, Math.PI * 2)
      ctx.setFillStyle(`rgba(${starColors[i % 4]},${(Math.random() * 0.35 + 0.15).toFixed(2)})`)
      ctx.fill()
    }

    // ---- 顶部品牌区 ----
    // 装饰圆环
    ctx.beginPath()
    ctx.arc(w / 2, 80, 36, 0, Math.PI * 2)
    ctx.setFillStyle('rgba(242,84,91,0.08)')
    ctx.fill()
    ctx.beginPath()
    ctx.arc(w / 2, 80, 24, 0, Math.PI * 2)
    ctx.setFillStyle('rgba(139,92,246,0.12)')
    ctx.fill()

    ctx.setTextAlign('center')
    ctx.setFillStyle('#2B2622')
    ctx.setFontSize(38)
    ctx.font = 'bold 38px sans-serif'
    ctx.fillText('星耀启程', w / 2, 90)

    ctx.setFillStyle('#A89F95')
    ctx.setFontSize(20)
    ctx.font = '20px sans-serif'
    ctx.fillText('人格深度测评报告', w / 2, 118)

    // 装饰线
    ctx.beginPath()
    ctx.moveTo(w / 2 - 60, 135)
    ctx.lineTo(w / 2 + 60, 135)
    ctx.setStrokeStyle('rgba(242,84,91,0.3)')
    ctx.setLineWidth(2)
    ctx.stroke()

    // ---- 姓名区 ----
    const profile = storage.getProfile() || {}
    const name = profile.name || '你'
    ctx.setFillStyle('#2B2622')
    ctx.setFontSize(30)
    ctx.font = 'bold 30px sans-serif'
    ctx.fillText(`${name} 的人格画像`, w / 2, 175)

    // 四体系标签
    const badges = this.data.typeBadges
    if (badges.length) {
      const tagY = 205
      let tagX = w / 2 - (badges.length * 90) / 2
      ctx.setFontSize(18)
      ctx.font = '18px sans-serif'
      badges.forEach((b, i) => {
        const tw = ctx.measureText(b).width + 24
        this._drawRoundRect(ctx, tagX, tagY, tw, 32, 16)
        ctx.setFillStyle('rgba(242,84,91,0.08)')
        ctx.fill()
        ctx.setStrokeStyle('rgba(242,84,91,0.25)')
        ctx.setLineWidth(1)
        ctx.stroke()
        ctx.setFillStyle('#F2545B')
        ctx.setTextAlign('center')
        ctx.fillText(b, tagX + tw / 2, tagY + 22)
        tagX += tw + 10
      })
    }

    // ---- 四体系快照卡片（2x2）----
    const cards = this.data.snapshotCards
    if (cards.length) {
      const cardStartY = 260
      const cardW = 250
      const cardH = 80
      const gap = 16
      const startX = (w - cardW * 2 - gap) / 2

      cards.forEach((c, i) => {
        const col = i % 2
        const row = Math.floor(i / 2)
        const cx = startX + col * (cardW + gap)
        const cy = cardStartY + row * (cardH + gap)

        // 卡片背景
        this._drawRoundRect(ctx, cx, cy, cardW, cardH, 12)
        ctx.setFillStyle('#FFFFFF')
        ctx.fill()
        // 顶部色条
        this._drawRoundRect(ctx, cx, cy, cardW, 5, 2)
        ctx.setFillStyle(c.color)
        ctx.fill()

        // 图标
        ctx.setFontSize(22)
        ctx.font = '22px sans-serif'
        ctx.setTextAlign('left')
        ctx.setFillStyle('#2B2622')
        ctx.fillText(c.icon, cx + 16, cy + 32)

        // 标题
        ctx.setFontSize(14)
        ctx.font = '14px sans-serif'
        ctx.setFillStyle('#A89F95')
        ctx.fillText(c.title, cx + 44, cy + 30)

        // 类型
        ctx.setFontSize(22)
        ctx.font = 'bold 22px sans-serif'
        ctx.setFillStyle(c.color)
        ctx.fillText(c.type, cx + 16, cy + 62)

        // 描述（截断）
        ctx.setFontSize(13)
        ctx.font = '13px sans-serif'
        ctx.setFillStyle('#6E665E')
        const desc = c.desc && c.desc.length > 20 ? c.desc.substring(0, 20) + '...' : (c.desc || '')
        ctx.fillText(desc, cx + 16, cy + 75)
      })
    }

    // ---- MBTI 迷你条形图 ----
    const mbtiBars = this.data.mbtiBars
    if (mbtiBars.length) {
      const chartY = 450
      this._drawChartTitle(ctx, w, chartY, 'MBTI 认知维度')

      mbtiBars.forEach((bar, i) => {
        const y = chartY + 30 + i * 32
        // 左标签
        ctx.setFontSize(16)
        ctx.font = 'bold 16px sans-serif'
        ctx.setTextAlign('left')
        ctx.setFillStyle(bar.left === bar.dominant ? '#3B9DEA' : '#C0B8AE')
        ctx.fillText(bar.left, 60, y + 14)
        ctx.setFontSize(11)
        ctx.font = '11px sans-serif'
        ctx.setFillStyle('#A89F95')
        ctx.fillText(bar.leftLabel, 78, y + 14)

        // 进度条
        const barX = 150
        const barW = 240
        const barH = 10
        this._drawRoundRect(ctx, barX, y + 6, barW, barH, 5)
        ctx.setFillStyle('#F0EAE2')
        ctx.fill()
        // 左侧蓝色
        this._drawRoundRect(ctx, barX, y + 6, barW * bar.leftPct / 100, barH, 5)
        ctx.setFillStyle('#3B9DEA')
        ctx.fill()
        // 右侧红色
        const rightX = barX + barW * bar.leftPct / 100
        this._drawRoundRect(ctx, rightX, y + 6, barW * bar.rightPct / 100, barH, 5)
        ctx.setFillStyle('#F2545B')
        ctx.fill()

        // 百分比
        ctx.setFontSize(11)
        ctx.font = '11px sans-serif'
        ctx.setFillStyle('#A89F95')
        ctx.setTextAlign('right')
        ctx.fillText(bar.leftPct + '%', barX - 6, y + 14)
        ctx.setTextAlign('left')
        ctx.fillText(bar.rightPct + '%', barX + barW + 6, y + 14)

        // 右标签
        ctx.setFontSize(16)
        ctx.font = 'bold 16px sans-serif'
        ctx.setFillStyle(bar.right === bar.dominant ? '#F2545B' : '#C0B8AE')
        ctx.fillText(bar.right, 420, y + 14)
        ctx.setFontSize(11)
        ctx.font = '11px sans-serif'
        ctx.setFillStyle('#A89F95')
        ctx.fillText(bar.rightLabel, 438, y + 14)
      })
    }

    // ---- 霍兰德迷你条形图 ----
    const hollandBars = this.data.hollandBars
    if (hollandBars.length) {
      const chartY = 600
      this._drawChartTitle(ctx, w, chartY, '霍兰德职业兴趣')

      hollandBars.forEach((bar, i) => {
        const y = chartY + 30 + i * 24
        ctx.setFontSize(15)
        ctx.font = 'bold 15px sans-serif'
        ctx.setTextAlign('left')
        ctx.setFillStyle(i === 0 ? '#F59E0B' : '#C0B8AE')
        ctx.fillText(bar.code, 60, y + 12)
        ctx.setFontSize(12)
        ctx.font = '12px sans-serif'
        ctx.setFillStyle('#6E665E')
        ctx.fillText(bar.name, 82, y + 12)

        const barX = 150
        const barW = 300
        const barH = 8
        this._drawRoundRect(ctx, barX, y + 4, barW, barH, 4)
        ctx.setFillStyle('#F5F0E8')
        ctx.fill()
        this._drawRoundRect(ctx, barX, y + 4, barW * bar.pct / 100, barH, 4)
        ctx.setFillStyle('#F59E0B')
        ctx.fill()

        ctx.setFontSize(12)
        ctx.font = 'bold 12px sans-serif'
        ctx.setTextAlign('right')
        ctx.setFillStyle('#2B2622')
        ctx.fillText(String(bar.score), 500, y + 12)
      })
    }

    // ---- 盖洛普迷你条形图 ----
    const gallupBars = this.data.gallupBars
    if (gallupBars.length) {
      const chartY = 770
      this._drawChartTitle(ctx, w, chartY, '盖洛普优势领域')

      gallupBars.forEach((bar, i) => {
        const y = chartY + 30 + i * 24
        // 色点
        ctx.beginPath()
        ctx.arc(66, y + 8, 5, 0, Math.PI * 2)
        ctx.setFillStyle(bar.color)
        ctx.fill()

        ctx.setFontSize(12)
        ctx.font = '12px sans-serif'
        ctx.setTextAlign('left')
        ctx.setFillStyle('#6E665E')
        ctx.fillText(bar.name, 76, y + 12)

        const barX = 200
        const barW = 250
        const barH = 8
        this._drawRoundRect(ctx, barX, y + 4, barW, barH, 4)
        ctx.setFillStyle('#F5F0E8')
        ctx.fill()
        this._drawRoundRect(ctx, barX, y + 4, barW * bar.pct / 100, barH, 4)
        ctx.setFillStyle(bar.color)
        ctx.fill()

        ctx.setFontSize(12)
        ctx.font = 'bold 12px sans-serif'
        ctx.setTextAlign('right')
        ctx.setFillStyle('#2B2622')
        ctx.fillText(String(bar.score), 500, y + 12)
      })
    }

    // ---- 简要解析文案 ----
    const summary = (storage.getResults() || {}).free_summary || ''
    if (summary) {
      const sumY = 900
      // 背景卡片
      this._drawRoundRect(ctx, 40, sumY, w - 80, 70, 12)
      ctx.setFillStyle('rgba(255,255,255,0.7)')
      ctx.fill()

      ctx.setFontSize(13)
      ctx.font = '13px sans-serif'
      ctx.setTextAlign('left')
      ctx.setFillStyle('#6E665E')
      // 自动换行
      const maxLen = 38
      const lines = []
      let text = summary.replace(/\n/g, ' ')
      while (text.length > maxLen && lines.length < 3) {
        lines.push(text.substring(0, maxLen))
        text = text.substring(maxLen)
      }
      if (text.length > 0 && lines.length < 3) lines.push(text)
      lines.forEach((line, i) => {
        ctx.fillText(line, 56, sumY + 20 + i * 18)
      })
    }

    // ---- 底部：二维码预留位 + slogan ----
    const qrY = 990
    // 二维码占位框
    this._drawRoundRect(ctx, w / 2 - 50, qrY, 100, 80, 10)
    ctx.setFillStyle('#F0EBE3')
    ctx.fill()
    ctx.setStrokeStyle('rgba(139,92,246,0.2)')
    ctx.setLineWidth(1)
    ctx.stroke()

    // 占位文字
    ctx.setFontSize(12)
    ctx.font = '12px sans-serif'
    ctx.setTextAlign('center')
    ctx.setFillStyle('#C0B8AE'
    )
    ctx.fillText('小程序码', w / 2, qrY + 35)
    ctx.fillText('（上线后补充）', w / 2, qrY + 52)

    // slogan
    ctx.setFillStyle('#F2545B')
    ctx.setFontSize(24)
    ctx.font = 'bold 24px sans-serif'
    ctx.fillText('发现你的独特光芒', w / 2, h - 55)

    ctx.setFillStyle('#A89F95'
    )
    ctx.setFontSize(14)
    ctx.font = '14px sans-serif'
    ctx.fillText('星耀启程 · 人格深度测评', w / 2, h - 30)

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

  /* 绘制图表标题 */
  _drawChartTitle(ctx, canvasW, y, title) {
    // 左侧装饰线
    ctx.beginPath()
    ctx.moveTo(50, y + 8)
    ctx.lineTo(60, y + 8)
    ctx.setStrokeStyle('#F2545B')
    ctx.setLineWidth(3)
    ctx.stroke()

    ctx.setTextAlign('left')
    ctx.setFillStyle('#2B2622')
    ctx.setFontSize(18)
    ctx.font = 'bold 18px sans-serif'
    ctx.fillText(title, 68, y + 13)
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

    let md = '# 星耀启程 · 完整人格深度报告\n\n'
    md += `生成时间：${report.generated_at || ''}\n\n---\n\n`
    report.sections.forEach((s) => {
      md += `${s.content}\n\n---\n\n`
    })

    const filePath = `${wx.env.USER_DATA_PATH}/星耀启程人格报告.md`
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
    return {
      title: '我的人格画像已生成，一起来发现你的独特光芒',
      path: '/pages/index/index'
    }
  }
})
