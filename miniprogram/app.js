/**
 * app.js — 星耀启程人格测评小程序入口
 * 启动时静默登录（wx.login → POST /api/login），token 存入本地缓存。
 */
const auth = require('./utils/auth')

App({
  globalData: {
    token: '',
    userInfo: null
  },

  onLaunch() {
    this.silentLogin()
  },

  /**
   * 静默登录：拿到 token 后存全局 + 缓存。
   * 后端未启动 / 非 mock 环境失败时静默降级，不影响页面展示。
   */
  silentLogin() {
    if (this.globalData.token) return Promise.resolve(this.globalData.token)
    return auth
      .login()
      .then((token) => {
        this.globalData.token = token
        return token
      })
      .catch((err) => {
        console.warn('[app] 静默登录失败:', err && err.message)
        return ''
      })
  },

  /** 确保已登录，供需要鉴权的流程调用 */
  ensureLogin() {
    if (this.globalData.token) return Promise.resolve(this.globalData.token)
    return this.silentLogin()
  }
})
