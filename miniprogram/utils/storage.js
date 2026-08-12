/**
 * storage.js — 本地缓存管理
 * 统一封装 wx.getStorageSync / wx.setStorageSync，避免散落的魔法字符串。
 */
const KEYS = {
  TOKEN: 'xy_token',
  PROFILE: 'xy_profile',
  SESSION: 'xy_session', // { session_id, total, questions }
  ANSWERS: 'xy_answers', // { [questionId]: optionIndex }
  QUIZ_INDEX: 'xy_quiz_index',
  RESULTS: 'xy_results', // submit 返回 { session_id, results, free_summary, ... }
  REPORT: 'xy_report' // 完整报告缓存（可选）
}

function get(key) {
  try {
    return wx.getStorageSync(key)
  } catch (e) {
    return null
  }
}

function set(key, value) {
  try {
    wx.setStorageSync(key, value)
  } catch (e) {
    // 存储失败静默处理
  }
}

function remove(key) {
  try {
    wx.removeStorageSync(key)
  } catch (e) {
    // ignore
  }
}

module.exports = {
  KEYS,

  getToken: () => get(KEYS.TOKEN),
  setToken: (t) => set(KEYS.TOKEN, t),
  clearToken: () => remove(KEYS.TOKEN),

  getProfile: () => get(KEYS.PROFILE),
  setProfile: (p) => (p ? set(KEYS.PROFILE, p) : remove(KEYS.PROFILE)),

  getSession: () => get(KEYS.SESSION),
  setSession: (s) => (s ? set(KEYS.SESSION, s) : remove(KEYS.SESSION)),

  getAnswers: () => get(KEYS.ANSWERS),
  setAnswers: (a) => (a ? set(KEYS.ANSWERS, a) : remove(KEYS.ANSWERS)),

  getQuizIndex: () => get(KEYS.QUIZ_INDEX) || 0,
  setQuizIndex: (i) => set(KEYS.QUIZ_INDEX, i),
  clearQuizIndex: () => remove(KEYS.QUIZ_INDEX),

  getResults: () => get(KEYS.RESULTS),
  setResults: (r) => (r ? set(KEYS.RESULTS, r) : remove(KEYS.RESULTS)),

  getReport: () => get(KEYS.REPORT),
  setReport: (r) => (r ? set(KEYS.REPORT, r) : remove(KEYS.REPORT)),

  /** 清除整个测评流程的进度（开始新测评前调用） */
  clearQuizFlow() {
    this.setSession(null)
    this.setAnswers(null)
    this.clearQuizIndex()
    this.setResults(null)
    this.setReport(null)
  }
}
