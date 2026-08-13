/**
 * app.js — 星耀启程人格测评小程序入口
 * 启动时初始化云开发 + 静默登录（wx.login → POST /api/login），token 存入本地缓存。
 */
const auth = require('./utils/auth')
const config = require('./utils/config')

App({
  globalData: {
    token: '',
    userInfo: null
  },

  onLaunch() {
    // 初始化云开发（云托管模式必须）
    if (config.CLOUD_ENV && wx.cloud) {
      wx.cloud.init({
        env: config.CLOUD_ENV,
        traceUser: true
      })
      console.log('[app] 云开发已初始化, env:', config.CLOUD_ENV)

      // 测试 callContainer 是否可用
      setTimeout(() => {
        wx.cloud.callContainer({
          config: { env: config.CLOUD_ENV },
          path: '/api/health',
          method: 'GET',
          header: { 'X-WX-SERVICE': config.CLOUD_SERVICE },
          success(res) {
            console.log('[app] callContainer 测试成功:', res.statusCode, res.data)
          },
          fail(err) {
            console.error('[app] callContainer 测试失败:', err)
          }
        })
      }, 500)
    }

    try {
      this.silentLogin()
    } catch (e) {
      console.warn('[app] 启动异常:', e)
    }
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
