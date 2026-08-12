/**
 * pages/profile/profile.js — 个人信息填写
 * 校验必填项（年龄/身份/目的）→ POST /api/session 创建会话并获取 120 题 → 缓存后跳转答题页。
 */
const api = require('../../utils/api')
const storage = require('../../utils/storage')
const labels = require('../../utils/labels')

Page({
  data: {
    name: '',
    age: '',
    birthDate: '',

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
    submitting: false
  },

  onNameInput(e) {
    this.setData({ name: e.detail.value })
  },

  onAgeInput(e) {
    this.setData({ age: e.detail.value })
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
    this.setData({ birthDate: e.detail.value })
  },

  validate() {
    const errors = {}
    const age = parseInt(this.data.age, 10)
    if (!this.data.age || isNaN(age) || age < 12 || age > 80) {
      errors.age = '请输入有效的年龄（12-80 岁）'
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
      age: parseInt(d.age, 10),
      role: d.roles[d.roleIndex].value,
      purpose: d.purposes[d.purposeIndex].value
    }
    if (d.name.trim()) profile.name = d.name.trim()
    if (d.genderIndex > 0) profile.gender = d.genders[d.genderIndex].value
    if (d.stateIndex > 0) profile.current_state = d.states[d.stateIndex].value
    if (d.horizonIndex > 0) profile.decision_horizon = d.horizons[d.horizonIndex].value
    if (d.birthDate) profile.birth_date = d.birthDate
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
