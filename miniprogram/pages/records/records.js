/**
 * pages/records/records.js — 我的测评记录
 *
 * 展示用户7天内（未付费）/ 30天内（已付费）的测评记录。
 * 未付费 → 点击跳转支付页继续解锁
 * 已付费 → 点击跳转完整报告页查看
 */
const api = require('../../utils/api')
const storage = require('../../utils/storage')

Page({
  data: {
    records: [],
    loading: true
  },

  onShow() {
    this.loadRecords()
  },

  loadRecords() {
    this.setData({ loading: true })
    api.getMySessions()
      .then((data) => {
        const records = (data.records || []).map((r) => ({
          ...r,
          dateText: this._formatDate(r.created_at)
        }))
        this.setData({ records, loading: false })
      })
      .catch(() => {
        this.setData({ loading: false })
        wx.showToast({ title: '加载失败', icon: 'none' })
      })
  },

  _formatDate(ts) {
    if (!ts) return ''
    const d = new Date(ts * 1000)
    const now = new Date()
    const diff = now - d
    const days = Math.floor(diff / 86400000)

    if (days === 0) return '今天'
    if (days === 1) return '昨天'
    if (days < 7) return `${days} 天前`
    if (days < 30) return `${Math.floor(days / 7)} 周前`

    const m = d.getMonth() + 1
    const day = d.getDate()
    return `${m}月${day}日`
  },

  onRecordTap(e) {
    const { id, paid } = e.currentTarget.dataset
    if (!id) return

    if (paid) {
      // 已付费 → 查看完整报告
      wx.navigateTo({ url: `/pages/result-full/result-full?session_id=${id}` })
    } else {
      // 未付费 → 跳转支付页继续解锁
      wx.navigateTo({ url: `/pages/pay/pay?session_id=${id}` })
    }
  },

  onGoHome() {
    wx.switchTab({ url: '/pages/index/index' })
  }
})
