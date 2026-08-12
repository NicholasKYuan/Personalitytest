/**
 * api.js — 后端 API 封装
 *
 * - 统一 wx.request 封装：JSON 请求、token 注入、业务码判断、401 自动重登重试
 * - USE_MOCK=true 时全部走 utils/mock.js，前端可独立预览
 * - 响应兼容两种格式：{ code, message, data } 包装 与 旧版裸数据
 *
 * 接口契约以 miniprogram/BACKEND_SPEC.md §4 为准。
 */
const config = require('./config')
const storage = require('./storage')
const mockApi = require('./mock')

/** 业务错误码（与 BACKEND_SPEC.md §3 一致） */
const ERR = {
  OK: 0,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER: 500,
  SESSION_NOT_OWNED: 1001,
  ORDER_CONFLICT: 1002,
  REPORT_GENERATING: 2001,
  REPORT_FAILED: 2002
}

function isMock() {
  return !!config.USE_MOCK
}

/**
 * 通用请求
 * @param {string} method GET/POST
 * @param {string} path 以 / 开头的接口路径
 * @param {object} data 请求体 / query 参数
 * @param {object} options { auth: boolean, retried: boolean }
 */
function request(method, path, data, options = {}) {
  const { auth = true, retried = false } = options
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json' }
    if (auth) {
      const token = storage.getToken()
      if (token) header.Authorization = 'Bearer ' + token
    }

    wx.request({
      url: config.BASE_URL + path,
      method,
      data,
      header,
      success(res) {
        const body = res.data

        if (res.statusCode >= 200 && res.statusCode < 300) {
          // 新版统一包装 { code, message, data }
          if (body && typeof body === 'object' && typeof body.code === 'number') {
            if (body.code === ERR.OK) {
              return resolve(body.data !== undefined ? body.data : body)
            }
            if (body.code === ERR.UNAUTHORIZED && auth && !retried) {
              // token 失效 → 重新登录后重试一次
              return reloginAndRetry(method, path, data, resolve, reject)
            }
            const err = new Error(body.message || `请求失败(${body.code})`)
            err.code = body.code
            return reject(err)
          }
          // 旧版裸数据
          return resolve(body)
        }

        // HTTP 层错误
        const msg =
          (body && (body.message || body.detail)) || `请求失败(${res.statusCode})`
        const err = new Error(msg)
        err.code = res.statusCode
        return reject(err)
      },
      fail() {
        reject(new Error('网络异常，请检查网络连接'))
      }
    })
  })
}

function reloginAndRetry(method, path, data, resolve, reject) {
  // 延迟 require 避免与 auth.js 循环依赖
  const auth = require('./auth')
  auth
    .login()
    .then(() => request(method, path, data, { retried: true }))
    .then(resolve)
    .catch((e) => reject(e))
}

/* ============================================================
   业务接口（USE_MOCK 开关在此处统一分发）
   ============================================================ */

/** POST /api/login — 微信登录（code → openid → token） */
function login(code, nickname, avatarUrl) {
  if (isMock()) return mockApi.login()
  return request(
    'POST',
    '/api/login',
    { code, nickname, avatar_url: avatarUrl },
    { auth: false }
  )
}

/** POST /api/session — 创建会话，返回 120 题（剥除 score） */
function createSession(profile) {
  if (isMock()) return mockApi.createSession(profile)
  return request('POST', '/api/session', { profile })
}

/** POST /api/submit — 提交答案，返回四体系结果 + free_summary */
function submitAnswers(sessionId, answers) {
  if (isMock()) return mockApi.submitAnswers(sessionId, answers)
  return request('POST', '/api/submit', { session_id: sessionId, answers })
}

/** POST /api/report/order — 创建 29.9 元付费订单，返回 wx.requestPayment 参数 */
function createOrder(sessionId) {
  if (isMock()) return mockApi.createOrder(sessionId)
  return request('POST', '/api/report/order', { session_id: sessionId })
}

/** GET /api/report/status — 查询支付 / 报告生成状态（支付成功后轮询） */
function getReportStatus(sessionId) {
  if (isMock()) return mockApi.getReportStatus(sessionId)
  return request('GET', `/api/report/status?session_id=${encodeURIComponent(sessionId)}`)
}

/** POST /api/report/detail — 付费后获取完整 AI 报告（markdown 章节） */
function getReportDetail(sessionId) {
  if (isMock()) return mockApi.getReportDetail(sessionId)
  return request('POST', '/api/report/detail', { session_id: sessionId })
}

/** POST /api/redeem/verify — 兑换密钥替代付费解锁报告 */
function redeemCode(sessionId, code) {
  if (isMock()) {
    // mock 模式：任何非空码都成功
    return new Promise((resolve) => {
      setTimeout(() => resolve({ paid: true, redeemed: true }), 600)
    })
  }
  return request('POST', '/api/redeem/verify', { session_id: sessionId, code })
}

/** GET /api/health — 健康检查 */
function getHealth() {
  if (isMock()) return Promise.resolve({ status: 'ok', bank_size: 2000, mock: true })
  return request('GET', '/api/health', null, { auth: false })
}

module.exports = {
  ERR,
  isMock,
  login,
  createSession,
  submitAnswers,
  createOrder,
  getReportStatus,
  getReportDetail,
  redeemCode,
  getHealth
}
