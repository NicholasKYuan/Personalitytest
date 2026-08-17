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
 * - CLOUD_ENV 有值时走 wx.cloud.callContainer()（云托管模式，免备案免白名单）
 * - CLOUD_ENV 为空时走 wx.request()（传统模式，需 HTTPS + 白名单）
 * @param {string} method GET/POST
 * @param {string} path 以 / 开头的接口路径
 * @param {object} data 请求体 / query 参数
 * @param {object} options { auth: boolean, retried: boolean }
 */
function request(method, path, data, options = {}) {
  const { auth = true, retried = false, cloudRetries = 0 } = options
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json' }
    if (auth) {
      const token = storage.getToken()
      if (token) header.Authorization = 'Bearer ' + token
    }

    const cloudConfigured = !!config.CLOUD_ENV
    const cloudReady = !!(wx.cloud && wx.cloud.callContainer)

    // 配置了云环境但 wx.cloud 不可用（基础库过低等）→ 明确报错，
    // 不允许降级到未备案的 BASE_URL（会导致 domain list 错误）
    if (cloudConfigured && !cloudReady) {
      const err = new Error('当前微信基础库过低，请升级微信后重试')
      err.code = -1
      return reject(err)
    }

    const useCloud = cloudConfigured && cloudReady

    // 直连降级仅开发版（开发者工具勾选"不校验合法域名"时）可用；
    // 体验版/正式版云托管默认域名无法加入 request 白名单（微信限制），
    // 直连必然失败，所以正式环境只走 callContainer + 重试
    const envVersion = (wx.getAccountInfoSync && wx.getAccountInfoSync().miniProgram.envVersion) || 'release'
    const fallbackAllowed = envVersion === 'develop'

    const handleSuccess = (res) => {
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
      // HTTP 401 也触发重新登录重试（后端未登录时返回 HTTP 401 而非业务码 401）
      if (res.statusCode === 401 && auth && !retried) {
        return reloginAndRetry(method, path, data, resolve, reject)
      }

      let msg = body && (body.message || body.detail)
      if (Array.isArray(msg)) {
        msg = msg.map((d) => (d && d.msg) || JSON.stringify(d)).join('；')
      } else if (msg && typeof msg !== 'string') {
        msg = JSON.stringify(msg)
      }
      msg = msg || `请求失败(${res.statusCode})`
      const err = new Error(msg)
      err.code = res.statusCode
      return reject(err)
    }

    const directRequest = () => {
      const baseUrl = useCloud
        ? config.CLOUD_FALLBACK_URL
        : config.BASE_URL || config.CLOUD_FALLBACK_URL || ''
      wx.request({
        url: baseUrl + path,
        method,
        data,
        header,
        success: handleSuccess,
        fail: (e) => {
          let msg2 = (e && (e.errMsg || e.message)) || '网络异常'
          // 域名不在白名单：给出可操作的指引，而不是裸报错
          if (msg2.includes('domain list') || msg2.includes('url not in')) {
            console.error('[api] 直连域名不在小程序白名单:', baseUrl)
            msg2 = '服务暂不可用，请稍后重试'
          }
          reject(new Error(msg2))
        }
      })
    }

    const handleFail = (err) => {
      const errMsg = (err && (err.errMsg || err.message)) || '网络异常'
      console.error('[api] request fail:', method, path, errMsg)

      // 云托管瞬时系统错误（102002 等，常见于服务冷启动/部署中）：
      // 最多重试 2 次 callContainer（延迟递增），多数瞬时错误自愈
      if (useCloud && cloudRetries < 2) {
        setTimeout(() => {
          request(method, path, data, { auth, retried, cloudRetries: cloudRetries + 1 })
            .then(resolve)
            .catch(reject)
        }, 800 * (cloudRetries + 1))
        return
      }

      // 重试耗尽 → 开发版降级直连（工具有"不校验合法域名"）；
      // 体验版/正式版直连必然被白名单拦截，直接报友好错误
      if (useCloud && config.CLOUD_FALLBACK_URL && fallbackAllowed) {
        console.log('[api] cloud.callContainer 重试仍失败，降级直连:', config.CLOUD_FALLBACK_URL + path)
        directRequest()
        return
      }

      const finalMsg = useCloud
        ? '服务暂时繁忙，请稍后重试'
        : errMsg
      reject(new Error(finalMsg))
    }

    if (useCloud) {
      // 云托管模式：通过 wx.cloud.callContainer 调用，免域名白名单
      wx.cloud.callContainer({
        config: { env: config.CLOUD_ENV },
        path: path,
        method,
        data,
        header: Object.assign({}, header, {
          'X-WX-SERVICE': config.CLOUD_SERVICE
        }),
        success: handleSuccess,
        fail: handleFail
      })
    } else {
      // 传统模式：wx.request
      directRequest()
    }
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
  return request('POST', '/api/session', profile)
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

/** GET /api/report/free — 获取免费预览结果（四体系分数+简述，无需付费） */
function getFreeResult(sessionId) {
  if (isMock()) return mockApi.getFreeResult(sessionId)
  return request('GET', `/api/report/free?session_id=${encodeURIComponent(sessionId)}`)
}

/** POST /api/report/detail — 付费后获取完整 AI 报告（markdown 章节） */
function getReportDetail(sessionId) {
  if (isMock()) return mockApi.getReportDetail(sessionId)
  return request('POST', '/api/report/detail', { session_id: sessionId })
}

/** POST /api/report/regenerate — 重新生成报告（已付费，不重复收费） */
function regenerateReport(sessionId) {
  if (isMock()) return Promise.resolve({ regenerating: true })
  return request('POST', '/api/report/regenerate', { session_id: sessionId })
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

/** GET /api/stats — 公开统计：完成测评人数 */
function getStats() {
  if (isMock()) return Promise.resolve({ completed_count: 12580 })
  return request('GET', '/api/stats', null, { auth: false })
}

/** GET /api/my/sessions — 查询我的测评记录（未付费7天/已付费30天） */
function getMySessions() {
  if (isMock()) {
    return Promise.resolve({
      records: [
        { session_id: 'mock-1', status: 'answered', paid: false, preview: '你是一个富有创造力的人...', created_at: Date.now() / 1000 - 86400 },
        { session_id: 'mock-2', status: 'ready', paid: true, preview: '你的领导力倾向明显...', created_at: Date.now() / 1000 - 172800 }
      ],
      total: 2
    })
  }
  return request('GET', '/api/my/sessions')
}

module.exports = {
  ERR,
  isMock,
  login,
  createSession,
  submitAnswers,
  createOrder,
  getReportStatus,
  getFreeResult,
  getReportDetail,
  regenerateReport,
  redeemCode,
  getHealth,
  getStats,
  getMySessions
}
