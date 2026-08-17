/**
 * pages/pay/pay.js — 付费解锁页
 *
 * 流程：createOrder 获取虚拟支付参数 → wx.requestVirtualPayment（mock 模式跳过） →
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

/** 等待时的温馨提示，轮播展示 */
const GEN_TIPS = [
  '正在分析您的九型人格特质…',
  '正在解读您的 MBTI 认知功能…',
  '正在匹配您的霍兰德职业方向…',
  '正在挖掘您的盖洛普优势主题…',
  '正在进行四体系交叉分析…',
  '即将完成，正在整理报告…'
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
    redeeming: false,
    generating: false,
    genProgress: 0,
    genTimeText: '预计需要 1-2 分钟',
    genTip: GEN_TIPS[0]
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

    // 付费状态以服务端为准：本地缓存可能是其他会话的 paid 标记，
    // 直接信任会导致未付费会话的按钮显示灰色「已解锁」无法付款。
    this.setData({ paid: false })
    api
      .getReportStatus(sessionId)
      .then((st) => {
        if (st && st.paid) {
          this.setData({ paid: true })
          // 同步本地标记（仅当前会话）
          storage.setResults({ ...results, session_id: sessionId, paid: true })
        }
      })
      .catch(() => {
        // 状态查询失败时保持未付费态，用户仍可正常发起支付
      })
  },

  onUnload() {
    this.stopPolling()
    this._stopProgressTimer()
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

        // mock 模式（paySig=MOCK_SIGN）：模拟支付成功，跳过真实调起
        if (params.paySig === 'MOCK_SIGN') {
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

  /** 调起虚拟支付（signData 为服务端生成的 JSON 字符串，必须原样传递） */
  doRequestPayment(params) {
    wx.requestVirtualPayment({
      mode: params.mode,
      signData: params.signData,
      paySig: params.paySig,
      signature: params.signature,
      success: () => {
        this.markPaid()
        this.startPolling()
      },
      fail: (res) => {
        this.setData({ paying: false })
        const msg = (res && res.errMsg) || ''
        const isCancel = msg.indexOf('cancel') > -1
        const tips = {
          15005: '登录态过期，请重新进入小程序再支付',
          15006: '支付签名错误，请稍后重试',
          15010: '道具未发布，请联系管理员',
          15011: '沙箱环境仅支持开发/体验版'
        }
        const tip = tips[res && res.errCode]
        wx.showToast({
          title: tip || (isCancel ? '支付已取消' : '支付失败，请重试'),
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
    this.setData({ generating: true, genProgress: 0, genTip: GEN_TIPS[0] })
    this.pollCount = 0
    this.genStartTime = Date.now()
    this._startProgressTimer()
    this.pollTimer = setTimeout(() => this.pollOnce(), 500)
  },

  /** 模拟进度条：前 30 秒快速增长到 60%，之后缓慢爬升到 95% */
  _startProgressTimer() {
    this._progressTimer = setInterval(() => {
      const elapsed = (Date.now() - this.genStartTime) / 1000
      let pct
      if (elapsed <= 30) {
        pct = Math.min(60, Math.round(elapsed * 2))
      } else {
        pct = Math.min(95, 60 + Math.round((elapsed - 30) * 0.6))
      }
      const tipIdx = Math.min(Math.floor(elapsed / 15), GEN_TIPS.length - 1)
      const remain = elapsed < 60 ? '预计需要 1-2 分钟' : '即将完成，请稍候…'
      this.setData({ genProgress: pct, genTip: GEN_TIPS[tipIdx], genTimeText: remain })
    }, 1000)
  },

  _stopProgressTimer() {
    if (this._progressTimer) {
      clearInterval(this._progressTimer)
      this._progressTimer = null
    }
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
          this._stopProgressTimer()
          this.setData({ genProgress: 100, genTimeText: '生成完成！' })
          setTimeout(() => {
            this.stopPolling()
            this.setData({ generating: false })
            this.goReport()
          }, 600)
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
        this._stopProgressTimer()
        this.stopPolling()
        this.setData({ generating: false, paying: false })
        wx.showToast({ title: (err && err.message) || '报告生成失败，请稍后重试', icon: 'none' })
      })
  },

  scheduleNextPoll() {
    this.pollCount = (this.pollCount || 0) + 1
    if (this.pollCount >= config.POLL_MAX_COUNT) {
      this._stopProgressTimer()
      this.stopPolling()
      this.setData({ generating: false, paying: false })
      wx.showToast({ title: '生成超时，请稍后在结果页重试', icon: 'none' })
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
    wx.redirectTo({
      url: `/pages/result-full/result-full?session_id=${encodeURIComponent(this.sessionId)}`
    })
  },

  onShareAppMessage() {
    return {
      title: '我的人格画像已生成，一起来发现你的独特光芒',
      path: '/pages/index/index'
    }
  }
})
