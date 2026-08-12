/**
 * pages/quiz/quiz.js — 答题页
 *
 * 核心交互：
 *  - 逐题渲染，进度条 + 百分比
 *  - 选项点击 800ms 后自动跳下一题（最后1题显示提交按钮）
 *  - 「上一题」回看修改；左右滑动切换
 *  - 每完成 40 / 80 题弹鼓励语
 *  - 离开页面自动保存进度（防意外退出丢失）
 */
const api = require('../../utils/api')
const storage = require('../../utils/storage')
const labels = require('../../utils/labels')

const AUTO_ADVANCE_MS = 800
const MILESTONE_MSGS = {
  40: '已完成 1/3，你对自我的探索正在深入',
  80: '已完成 2/3，马上就能看到你的专属结果了'
}

Page({
  data: {
    currentIndex: 0,
    total: 0,
    progressText: '第 1 / 120 题',
    progressPct: 0,
    question: null,
    options: [],
    categoryLabel: '',
    scaleLabel: '',
    selectedIndex: -1,
    showSubmit: false
  },

  onLoad() {
    const session = storage.getSession()
    if (!session || !session.questions || session.questions.length === 0) {
      wx.redirectTo({ url: '/pages/profile/profile' })
      return
    }

    this.sessionId = session.session_id
    this.questions = session.questions
    this.total = session.total || session.questions.length
    // 进度（题目/答案）保存在实例属性，避免大对象 setData
    this.answers = storage.getAnswers() || {}
    this.currentIndex = storage.getQuizIndex()
    if (this.currentIndex >= this.questions.length) this.currentIndex = 0
    this.autoTimer = null
    this.transitioning = false
    this.touchStartX = 0
    this.touchStartY = 0

    this.setData({ total: this.total }, () => this.renderQuestion())
  },

  onUnload() {
    this.clearAutoTimer()
    this.saveProgress()
  },

  onHide() {
    this.clearAutoTimer()
    this.saveProgress()
  },

  /* ---------- 渲染 ---------- */
  renderQuestion() {
    this.clearAutoTimer()
    this.transitioning = false

    const q = this.questions[this.currentIndex]
    if (!q) return

    const currentAnswer = this.answers[q.id]
    const answeredCount = Object.keys(this.answers).length

    this.setData({
      currentIndex: this.currentIndex,
      question: {
        id: q.id,
        stem: q.stem
      },
      options: q.options.map((o, i) => ({ ...o, index: i })),
      categoryLabel: labels.CATEGORY_LABELS[q.category] || q.category || '综合',
      scaleLabel: labels.SCALE_LABELS[q.scale] || '',
      selectedIndex: typeof currentAnswer === 'number' ? currentAnswer : -1,
      progressText: `第 ${this.currentIndex + 1} / ${this.total} 题`,
      progressPct: Math.max(
        Math.round((answeredCount / this.total) * 100),
        Math.round(((this.currentIndex + 1) / this.total) * 100)
      ),
      showSubmit: false
    })

    // 最后1题已答 → 显示提交按钮
    if (this.currentIndex === this.questions.length - 1 && typeof currentAnswer === 'number') {
      this.setData({ showSubmit: true })
    }
  },

  /* ---------- 选项点击 ---------- */
  onOptionTap(e) {
    if (this.transitioning) return
    const idx = Number(e.currentTarget.dataset.index)
    const q = this.questions[this.currentIndex]
    if (!q) return
    if (this.answers[q.id] === idx) return

    // 保存答案 + UI 高亮
    this.answers[q.id] = idx
    this.setData({ selectedIndex: idx })
    wx.vibrateShort({ type: 'light' })
    this.saveProgress()

    const isLast = this.currentIndex === this.questions.length - 1
    if (!isLast) {
      // 800ms 后自动跳下一题
      this.clearAutoTimer()
      this.transitioning = true
      this.autoTimer = setTimeout(() => {
        this.transitioning = false
        this.currentIndex += 1
        this.checkMilestone()
        this.renderQuestion()
      }, AUTO_ADVANCE_MS)
    } else {
      this.setData({ showSubmit: true })
    }
  },

  /* ---------- 里程碑鼓励 ---------- */
  checkMilestone() {
    const idx = this.currentIndex
    const msg = MILESTONE_MSGS[idx]
    if (!msg) return
    wx.showModal({
      title: '探索进行中',
      content: msg,
      showCancel: false,
      confirmText: '继续'
    })
  },

  /* ---------- 导航 ---------- */
  onPrev() {
    this.clearAutoTimer()
    this.transitioning = false
    if (this.currentIndex > 0) {
      this.currentIndex -= 1
      this.renderQuestion()
    }
  },

  /* ---------- 手势：左滑下一题 / 右滑上一题 ---------- */
  onTouchStart(e) {
    const t = e.touches && e.touches[0]
    if (!t) return
    this.touchStartX = t.clientX
    this.touchStartY = t.clientY
  },

  onTouchEnd(e) {
    const t = e.changedTouches && e.changedTouches[0]
    if (!t) return
    const dx = t.clientX - this.touchStartX
    const dy = t.clientY - this.touchStartY
    if (Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) * 1.5) return
    if (dx < 0) {
      // 左滑：下一题（跳过未作答也允许跳转，仅作为辅助导航）
      this.clearAutoTimer()
      this.transitioning = false
      if (this.currentIndex < this.questions.length - 1) {
        this.currentIndex += 1
        this.renderQuestion()
      }
    } else {
      this.onPrev()
    }
  },

  /* ---------- 提交 ---------- */
  onSubmitTap() {
    this.clearAutoTimer()
    this.transitioning = false

    // 校验未作答题目
    const unanswered = this.questions.filter((q) => typeof this.answers[q.id] !== 'number')
    if (unanswered.length > 0) {
      wx.showToast({ title: `还有 ${unanswered.length} 题未作答`, icon: 'none' })
      const idx = this.questions.indexOf(unanswered[0])
      this.currentIndex = idx
      this.renderQuestion()
      return
    }

    wx.showModal({
      title: '确认提交',
      content: '确认提交全部答案？提交后将无法修改',
      confirmText: '确认提交',
      cancelText: '再想想',
      success: (res) => {
        if (res.confirm) this.doSubmit()
      }
    })
  },

  doSubmit() {
    wx.showLoading({ title: '正在分析...', mask: true })
    const answers = this.questions.map((q) => ({
      question_id: q.id,
      option_index: this.answers[q.id]
    }))

    api
      .submitAnswers(this.sessionId, answers)
      .then((data) => {
        // 结果缓存 + 清空答题进度
        storage.setResults(data)
        storage.setSession(null)
        storage.setAnswers(null)
        storage.clearQuizIndex()
        wx.hideLoading()
        wx.redirectTo({ url: '/pages/result-free/result-free' })
      })
      .catch((err) => {
        wx.hideLoading()
        wx.showToast({ title: err.message || '提交失败，请检查网络后重试', icon: 'none' })
      })
  },

  /* ---------- 进度保存 ---------- */
  saveProgress() {
    storage.setAnswers(this.answers)
    storage.setQuizIndex(this.currentIndex)
  },

  clearAutoTimer() {
    if (this.autoTimer) {
      clearTimeout(this.autoTimer)
      this.autoTimer = null
    }
  }
})
