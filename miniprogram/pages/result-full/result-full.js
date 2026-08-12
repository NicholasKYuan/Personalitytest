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

Page({
  data: {
    loading: true,
    greet: '',
    typeBadges: [],
    generatedAt: '',
    sections: [],
    posterW: 600,
    posterH: 900
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
    const sections = (report.sections || []).map((s, i) => ({
      index: String(i + 1).padStart(2, '0'),
      title: s.title || `章节 ${i + 1}`,
      html: markdown.render(s.content)
    }))

    const r = report.results || {}
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

    this.setData({
      loading: false,
      greet: `你好，${name}！这是你的完整人格画像`,
      typeBadges: badges.filter(Boolean),
      generatedAt: report.generated_at || '',
      sections
    })
  },

  /* ============================================================
     生成分享海报
     ============================================================ */
  onPoster() {
    if (this.posting) return
    this.posting = true
    wx.showLoading({ title: '正在生成海报...', mask: true })

    const w = this.data.posterW
    const h = this.data.posterH
    const ctx = wx.createCanvasContext('posterCanvas', this)

    // 背景渐变（暖光）
    const grad = ctx.createLinearGradient(0, 0, 0, h)
    grad.addColorStop(0, '#FFF3E8')
    grad.addColorStop(0.4, '#FAF7F2')
    grad.addColorStop(1, '#F5F0FF')
    ctx.setFillStyle(grad)
    ctx.fillRect(0, 0, w, h)

    // 星光点缀（彩虹色）
    const starColors = ['245,158,11', '139,92,246', '242,84,91', '59,158,216']
    for (let i = 0; i < 60; i++) {
      const x = Math.random() * w
      const y = Math.random() * h
      const r = Math.random() * 1.6 + 0.6
      ctx.beginPath()
      ctx.arc(x, y, r, 0, Math.PI * 2)
      ctx.setFillStyle(`rgba(${starColors[i % 4]},${(Math.random() * 0.4 + 0.25).toFixed(2)})`)
      ctx.fill()
    }

    // 标题
    ctx.setTextAlign('center')
    ctx.setFillStyle('#2B2622')
    ctx.setFontSize(44)
    ctx.fillText('星耀启程 · 人格画像', w / 2, 130)

    // 姓名
    const name = (storage.getProfile() && storage.getProfile().name) || ''
    ctx.setFillStyle('#6E665E')
    ctx.setFontSize(34)
    ctx.fillText(`${name ? name + '，' : ''}这是你的人格画像`, w / 2, 210)

    // 四体系结果卡片
    const badges = this.data.typeBadges
    const cardW = 460
    const cardH = 86
    const startY = 290
    const gap = 22
    badges.forEach((b, i) => {
      const y = startY + i * (cardH + gap)
      // 圆角白卡
      ctx.setFillStyle('#FFFFFF')
      this.roundRectPath(ctx, (w - cardW) / 2, y, cardW, cardH, 18)
      ctx.fill()
      // 序号圆点
      ctx.beginPath()
      ctx.arc(w / 2 - 150, y + cardH / 2, 14, 0, Math.PI * 2)
      ctx.setFillStyle('#F2545B')
      ctx.fill()
      ctx.setFillStyle('#FFFFFF')
      ctx.setFontSize(22)
      ctx.fillText(String(i + 1), w / 2 - 150, y + cardH / 2 + 8)
      // 类型文字
      ctx.setFontSize(28)
      ctx.fillStyle = '#2B2622'
      ctx.fillText(b, w / 2, y + cardH / 2 + 10)
    })

    // 底部 slogan
    ctx.setFillStyle('#F2545B')
    ctx.setFontSize(32)
    ctx.fillText('发现你的独特光芒', w / 2, h - 160)
    ctx.setFillStyle('#A89F95')
    ctx.setFontSize(22)
    ctx.fillText('微信扫一扫 · 开启你的人格测评', w / 2, h - 110)

    ctx.draw(false, () => {
      // 等绘制完成再导出
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
      }, 250)
    })
  },

  roundRectPath(ctx, x, y, w, h, r) {
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
