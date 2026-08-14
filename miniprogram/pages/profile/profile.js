/**
 * pages/profile/profile.js — 个人信息填写
 * 校验必填项（出生日期/身份/目的）→ POST /api/session 创建会话并获取 120 题 → 缓存后跳转答题页。
 * 出生日期必填，年龄自动从出生日期计算。
 */
const api = require('../../utils/api')
const storage = require('../../utils/storage')
const labels = require('../../utils/labels')

/** 从出生日期字符串（YYYY-MM-DD）计算年龄 */
function calcAge(birthStr) {
  if (!birthStr) return 0
  const birth = new Date(birthStr)
  const now = new Date()
  let age = now.getFullYear() - birth.getFullYear()
  const mDiff = now.getMonth() - birth.getMonth()
  if (mDiff < 0 || (mDiff === 0 && now.getDate() < birth.getDate())) {
    age--
  }
  return age
}

Page({
  data: {
    name: '',
    age: '',
    birthDate: '',
    todayDate: '',

    // 选择器：第一项为占位项（value 为空表示未选）
    genders: [{ label: '请选择（可选）', value: '' }].concat(labels.GENDER_OPTIONS),
    roles: [{ label: '请选择你的当前身份', value: '' }].concat(labels.ROLE_OPTIONS),
    purposes: [{ label: '请选择本次测评的目的', value: '' }].concat(labels.PURPOSE_OPTIONS),
    states: [{ label: '请选择（可选）', value: '' }].concat(labels.STATE_OPTIONS),
    horizons: [{ label: '请选择（可选）', value: '' }].concat(labels.HORIZON_OPTIONS),

    genderIndex: 0,
    roleIndex: 0,
    purposeIndex: 0,
    stateIndex: 0,
    horizonIndex: 0,

    errors: {},
    submitting: false,
    focusField: ''
  },

  onLoad() {
    // 日期选择器上限为今天
    const now = new Date()
    const yyyy = now.getFullYear()
    const mm = String(now.getMonth() + 1).padStart(2, '0')
    const dd = String(now.getDate()).padStart(2, '0')
    this.setData({ todayDate: `${yyyy}-${mm}-${dd}` })
  },

  onInputFocus(e) {
    this.setData({ focusField: e.currentTarget.dataset.field || '' })
  },

  onInputBlur() {
    this.setData({ focusField: '' })
  },

  onNameInput(e) {
    this.setData({ name: e.detail.value })
  },

  onGenderChange(e) {
    this.setData({ genderIndex: Number(e.detail.value) })
  },

  onRoleChange(e) {
    this.setData({ roleIndex: Number(e.detail.value) })
  },

  onPurposeChange(e) {
    this.setData({ purposeIndex: Number(e.detail.value) })
  },

  onStateChange(e) {
    this.setData({ stateIndex: Number(e.detail.value) })
  },

  onHorizonChange(e) {
    this.setData({ horizonIndex: Number(e.detail.value) })
  },

  onBirthChange(e) {
    const birthDate = e.detail.value
    const age = calcAge(birthDate)
    this.setData({ birthDate, age: age > 0 ? String(age) : '' })
  },

  validate() {
    const errors = {}
    if (!this.data.birthDate) {
      errors.birthDate = '请选择出生年月日'
    } else {
      const age = calcAge(this.data.birthDate)
      if (age < 12 || age > 80) {
        errors.birthDate = '年龄需在 12-80 岁之间'
      }
    }
    if (this.data.roleIndex === 0) {
      errors.role = '请选择你的当前身份'
    }
    if (this.data.purposeIndex === 0) {
      errors.purpose = '请选择测评目的'
    }
    return errors
  },

  buildProfile() {
    const d = this.data
    const profile = {
      age: calcAge(d.birthDate),
      birth_date: d.birthDate,
      role: d.roles[d.roleIndex].value,
      purpose: d.purposes[d.purposeIndex].value
    }
    if (d.name.trim()) profile.name = d.name.trim()
    if (d.genderIndex > 0) profile.gender = d.genders[d.genderIndex].value
    if (d.stateIndex > 0) profile.current_state = d.states[d.stateIndex].value
    if (d.horizonIndex > 0) profile.decision_horizon = d.horizons[d.horizonIndex].value
    return profile
  },

  onSubmit() {
    if (this.data.submitting) return

    const errors = this.validate()
    if (Object.keys(errors).length > 0) {
      this.setData({ errors })
      wx.showToast({ title: '请完善必填信息', icon: 'none' })
      return
    }

    this.setData({ errors: {}, submitting: true })
    wx.showLoading({ title: '生成题目中...', mask: true })

    const profile = this.buildProfile()
    storage.setProfile(profile)

    api
      .createSession(profile)
      .then((data) => {
        if (!data.questions || data.questions.length === 0) {
          throw new Error('未获取到测评题目，请重试')
        }
        // 清理旧流程，缓存新会话
        storage.setAnswers(null)
        storage.clearQuizIndex()
        storage.setSession({
          session_id: data.session_id,
          total: data.total || data.questions.length,
          questions: data.questions
        })
        wx.hideLoading()
        wx.redirectTo({ url: '/pages/quiz/quiz' })
      })
      .catch((err) => {
        wx.hideLoading()
        wx.showToast({ title: err.message || '网络异常，请重试', icon: 'none' })
      })
      .finally(() => {
        this.setData({ submitting: false })
      })
  }
})
