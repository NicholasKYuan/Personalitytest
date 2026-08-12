/**
 * auth.js — 微信登录流程封装
 *
 * wx.login() 获取 code → POST /api/login（mock 模式下返回假 token）
 * → token 存入本地缓存。上层通过 app.ensureLogin() / api 统一鉴权。
 */
const api = require('./api')
const storage = require('./storage')

/**
 * 登录并缓存 token
 * @returns {Promise<string>} token
 */
function login() {
  return new Promise((resolve, reject) => {
    // mock 模式无需真实 wx.login
    if (api.isMock()) {
      api
        .login()
        .then((data) => {
          storage.setToken(data.token)
          resolve(data.token)
        })
        .catch(reject)
      return
    }

    wx.login({
      success(res) {
        if (!res.code) {
          reject(new Error('微信登录失败：未获取到 code'))
          return
        }
        api
          .login(res.code)
          .then((data) => {
            storage.setToken(data.token)
            resolve(data.token)
          })
          .catch((err) => {
            storage.clearToken()
            reject(err)
          })
      },
      fail(err) {
        reject(new Error('微信登录失败：' + (err.errMsg || '')))
      }
    })
  })
}

module.exports = { login }
