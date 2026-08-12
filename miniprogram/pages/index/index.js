/**
 * pages/index/index.js — 首页
 * 品牌展示、测试说明、用户评价、开始入口；进入时检查未完成会话并引导续测。
 */
const storage = require('../../utils/storage')

Page({
  data: {
    systems: ['九型人格', 'MBTI', '霍兰德', '盖洛普'],
    features: [
      { title: '120 题精准测评，融合四大权威体系' },
      { title: 'AI 深度分析，9000+ 字个性化报告' },
      { title: '职业方向指引，发现你的独特优势' },
      { title: '约 15 分钟完成，随时暂停续测' }
    ],
    reviews: [
      { text: '测完真的很准，四体系交叉分析让我看到了盲区', author: '大三学生' },
      { text: '原来我的优势是这样组合的，职业方向一下清晰了', author: '在职 5 年设计师' },
      { text: '题目设计很用心，15 分钟不知不觉就做完了', author: '高二学生' },
      { text: '朋友推荐来测的，报告比我预想的深刻很多', author: '创业者' }
    ]
  },

  onShow() {
    this.checkUnfinishedQuiz()
  },

  /** 检查本地是否有未完成的会话，弹窗引导继续 */
  checkUnfinishedQuiz() {
    const session = storage.getSession()
    const answers = storage.getAnswers()
    if (!session || !answers) return
    const answeredCount = Object.keys(answers).length
    if (answeredCount === 0) return

    wx.showModal({
      title: '欢迎回来',
      content: `您有未完成的测评（已完成 ${answeredCount} 题），是否继续？`,
      confirmText: '继续测评',
      cancelText: '重新开始',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({ url: '/pages/quiz/quiz' })
        } else {
          storage.clearQuizFlow()
        }
      }
    })
  },

  onStart() {
    wx.navigateTo({ url: '/pages/profile/profile' })
  },

  onShareAppMessage() {
    return {
      title: '四体系融合人格测评，发现你的独特光芒',
      path: '/pages/index/index',
      desc: '九型人格 / MBTI / 霍兰德 / 盖洛普，120 题免费测评'
    }
  }
})
