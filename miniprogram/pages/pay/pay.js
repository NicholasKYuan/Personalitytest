/**
 * pages/pay/pay.js — 付费解锁页
 *
 * 流程：createOrder 获取支付参数 → wx.requestPayment（mock 模式跳过） →
 *       支付成功后轮询 /api/report/status → report ready → 跳转完整报告页。
 */
const api = require('../../utils/api')
const config = require('../../utils/config')
const storage = require('../../utils/storage')

/** 六大章节价值清单（文案与完整报告章节一一对应） */
const CHAPTERS = [
  { title: '九型人格深度解读', words: '约 1,800 字', preview: '核心特质、内在动机、隐藏盲区与专属成长方向…' },
  { title: 'MBTI 认知功能分析', words: '约 1,600 字', preview: '你的认知功能栈如何驱动思考、决策与行动…' },
  { title: '霍兰德职业方向推荐', words: '约 1,400 字', preview: '适配的行业与岗位方向、职业发展路径建议…' },
  { title: '盖洛普优势发挥指南', words: '约 1,500 字', preview: '核心优势主题盘点与放大优势的具体方法…' },
  { title: '四体系交叉协同解读', words: '约 2,000 字', preview: '四个体系如何互相印证，形成你的独特画像闭环…' },
  { title: '传统易学辅助参考', words: '约 1,200 字', preview: '结合出生信息的命局视角，与心理画像互相呼应…' }
]

const BENEFITS = [
  '一次付费，永久查看与分享你的完整报告',
  '90 天内免费获取一次报告更新（题目扩充后）',
  'AI 生成内容仅供参考，不构成任何专业诊断'
]

Page({
  data: {
    chapters: CHAPTERS,
    benefits: BENEFITS,
    paying: false,
    paid: false,
    price: config.PRICE_CN,
    originalPrice: config.PRICE_ORIGINAL_CN,
    redeemInput: '',
    redeeming: false
  },

  onLoad(options) {
    // 优先取 URL 参数，兜底取本地缓存的结果
    const results = storage.getResults() || {}
    const sessionId = (options && options.session_id) || results.session_id || ''
    if (!sessionId) {
      wx.showToast({ title: '会话不存在，请重新测评', icon: 'none' })
      setTimeout(() => wx.redirectTo({ url: '/pages/result-free/result-free' }), 1200)
      return
    }
    this.sessionId = sessionId

    // 已支付过 → 直接进入报告页
    if (results.paid) {
      this.setData({ paid: true })
    }
  },

  onUnload() {
    this.stopPolling()
  },

  /* ============================================================
     支付主流程
     ============================================================ */
  onPay() {
    if (this.data.paying) return
    if (this.data.paid) {
      this.goReport()
      return
    }

    this.setData({ paying: true })
    api
      .createOrder(this.sessionId)
      .then((data) => {
        // 服务端判定已支付 → 直接进入报告
        if (data && data.paid) {
          this.markPaid()
          this.startPolling()
          return
        }
        const params = data && data.pay_params
        if (!params) {
          throw new Error('未获取到支付参数')
        }

        // mock 模式（paySign=MOCK_SIGN）：模拟支付成功，跳过真实调起
        if (params.paySign === 'MOCK_SIGN') {
          setTimeout(() => {
            this.markPaid()
            this.startPolling()
          }, 600)
          return
        }

        this.doRequestPayment(params)
      })
      .catch((err) => {
        this.setData({ paying: false })
        wx.showToast({ title: (err && err.message) || '订单创建失败，请重试', icon: 'none' })
      })
  },

  /** 调起微信支付 */
  doRequestPayment(params) {
    wx.requestPayment({
      ...params,
      success: () => {
        this.markPaid()
        this.startPolling()
      },
      fail: (res) => {
        this.setData({ paying: false })
        const msg = (res && res.errMsg) || ''
        const isCancel = msg.indexOf('cancel') > -1
        wx.showToast({
          title: isCancel ? '支付已取消' : '支付失败，请重试',
          icon: 'none'
        })
      }
    })
  },

  /** 支付成功 → 本地标记已付费 */
  markPaid() {
    const results = storage.getResults() || {}
    storage.setResults({ ...results, paid: true, session_id: this.sessionId })
    this.setData({ paid: true, paying: false })
  },

  /* ============================================================
     报告生成状态轮询
     ============================================================ */
  startPolling() {
    wx.showLoading({ title: 'AI 正在生成报告...', mask: true })
    this.pollCount = 0
    this.pollTimer = setTimeout(() => this.pollOnce(), 500)
  },

  pollOnce() {
    api
      .getReportStatus(this.sessionId)
      .then((status) => {
        const ready =
          status &&
          (status.is_ready ||
            status.report_status === 'ready' ||
            status.report_status === 'failed')
        if (ready) {
          this.stopPolling()
          wx.hideLoading()
          this.goReport()
          return
        }
        this.scheduleNextPoll()
      })
      .catch((err) => {
        // 生成中/会话处理中错误码（2001）按继续轮询处理
        if (err && err.code === api.ERR.REPORT_GENERATING) {
          this.scheduleNextPoll()
          return
        }
        this.stopPolling()
        wx.hideLoading()
        wx.showToast({ title: (err && err.message) || '报告生成失败，请稍后重试', icon: 'none' })
        this.setData({ paying: false })
      })
  },

  scheduleNextPoll() {
    this.pollCount = (this.pollCount || 0) + 1
    if (this.pollCount >= config.POLL_MAX_COUNT) {
      this.stopPolling()
      wx.hideLoading()
      wx.showToast({ title: '生成超时，请稍后在结果页重试', icon: 'none' })
      this.setData({ paying: false })
      return
    }
    this.pollTimer = setTimeout(() => this.pollOnce(), config.POLL_INTERVAL_MS)
  },

  stopPolling() {
    if (this.pollTimer) {
      clearTimeout(this.pollTimer)
      this.pollTimer = null
    }
  },

  /* ============================================================
     兑换密钥
     ============================================================ */
  onRedeemInput(e) {
    this.setData({ redeemInput: e.detail.value })
  },

  onRedeem() {
    const code = (this.data.redeemInput || '').trim()
    if (!code) {
      wx.showToast({ title: '请输入兑换码', icon: 'none' })
      return
    }
    this.setData({ redeeming: true })
    api
      .redeemCode(this.sessionId, code)
      .then((data) => {
        if (data && data.paid) {
          this.markPaid()
          this.startPolling()
        }
      })
      .catch((err) => {
        this.setData({ redeeming: false })
        wx.showToast({ title: (err && err.message) || '兑换失败，请检查兑换码', icon: 'none' })
      })
  },

  /* ============================================================
     跳转
     ============================================================ */
  goReport() {
    wx.redirectTo({ url: '/pages/result-full/result-full' })
  },

  onShareAppMessage() {
    return {
      title: '我的人格画像已生成，一起来发现你的独特光芒',
      path: '/pages/index/index'
    }
  }
})
