/**
 * labels.js — 中文字典与枚举映射
 * 与后端 profile-schema.json / scorer.py / selector 的枚举保持一致。
 */

/* ---------- 题目类别 ---------- */
const CATEGORY_LABELS = {
  'interpersonal-relationship': '人际交往',
  'decision-making': '决策方式',
  'stress-response': '压力应对',
  'motivation-value': '动力与价值观',
  'learning-cognition': '学习与认知',
  'work-career': '工作与职业',
  'emotion-self': '情绪与自我',
  'action-habit': '行为习惯',
  'future-vision': '未来展望',
  'conflict-choice': '冲突与选择'
}

/* ---------- 题型 ---------- */
const SCALE_LABELS = {
  'forced-choice': '场景选择',
  'likert-4': '程度选择',
  'likert-5': '程度选择',
  'likert-7': '程度选择',
  'ranking': '排序题'
}

/* ---------- 九型人格 ---------- */
const ENNEAGRAM_NAMES = {
  1: '完美主义者',
  2: '助人者',
  3: '成就者',
  4: '个人主义者',
  5: '观察者',
  6: '忠诚者',
  7: '热情者',
  8: '挑战者',
  9: '和平者'
}

const ENNEAGRAM_DESC = {
  1: '你追求精确与秩序，内心有强烈的是非感',
  2: '你天生善于关爱他人，在给予中找到自我价值',
  3: '你善于设定目标并高效达成，渴望被认可',
  4: '你感受力深邃，追求独特的自我表达',
  5: '你善于深度思考，在理解世界中获得安全感',
  6: '你谨慎可靠，善于预判风险并做好准备',
  7: '你充满好奇心，善于发现生活中的可能性',
  8: '你天生意志力强，善于掌控局面和保护他人',
  9: '你温和包容，善于调和矛盾、维持和谐'
}

/* ---------- MBTI ---------- */
const MBTI_DESC = {
  ENTJ: '天生的领导者，善于战略规划和高效执行',
  ENFJ: '天生的引导者，善于鼓舞并成就他人',
  ESTJ: '务实的管理者，善于组织与执行',
  ESFJ: '热心的组织者，善于维护团队氛围',
  ESTP: '敏捷的行动派，善于把握当下机会',
  ESFP: '热情的表演者，善于活跃现场气氛',
  ENTP: '机智的辩论家，善于挑战常规思维',
  ENFP: '热情的探索者，善于发现各种可能性',
  INTJ: '冷静的战略家，善于长远规划',
  INFJ: '洞察的倡导者，善于深度理解他人',
  ISTJ: '可靠的守卫者，坚持原则与秩序',
  ISFJ: '温和的守护者，默默守护身边人的安宁',
  ISTP: '冷静的观察者，善于解决实际问题',
  ISFP: '柔和的艺术家，用感受丈量世界',
  INTP: '独立的思考者，追求逻辑自洽',
  INFP: '理想主义的诗人，内心有坚定的价值观'
}

/* ---------- 霍兰德 ---------- */
const HOLLAND_NAMES = {
  R: '实际型',
  I: '研究型',
  A: '艺术型',
  S: '社会型',
  E: '企业型',
  C: '常规型'
}

const HOLLAND_DESC = {
  R: '动手实践是你的强项，适合工程技术方向',
  I: '你善于分析钻研，适合研究研发方向',
  A: '你富有创造力，适合设计、写作、艺术方向',
  S: '你善于与人互动，适合教育、咨询、服务方向',
  E: '你善于影响他人，适合管理、销售、创业方向',
  C: '你细致有序，适合财务、行政、运营方向'
}

/* ---------- 盖洛普 ---------- */
const GALLUP_DOMAINS = {
  executing: '执行力',
  influencing: '影响力',
  relationship_building: '关系建立',
  strategic_thinking: '战略思维'
}

const GALLUP_DOMAIN_DESC = {
  executing: '你善于把事情做成，行动力强、注重结果',
  influencing: '你善于掌控局面，能带动他人追随你的方向',
  relationship_building: '你善于建立深度联结，是团队的凝聚力核心',
  strategic_thinking: '你善于分析信息，在复杂局面中找到最优解'
}

const GALLUP_THEMES = {
  achiever: '成就', activator: '行动', adaptability: '适应',
  analytical: '分析', arranger: '统筹', belief: '信仰',
  command: '统率', communication: '沟通', competition: '竞争',
  connectedness: '关联', context: '回顾', consistency: '公平',
  deliberative: '审慎', developer: '伯乐', discipline: '纪律',
  empathy: '体谅', focus: '专注', futuristic: '前瞻',
  harmony: '和谐', ideation: '理念', includer: '包容',
  individualization: '个别', input: '搜集', intellection: '思维',
  learner: '学习', maximizer: '完美', positivity: '积极',
  relator: '交往', responsibility: '责任', restorative: '排难',
  self_assurance: '自信', significance: '追求', strategic: '战略',
  woo: '取悦'
}

/* ---------- 个人信息表单选项（与 profile-schema.json 一致） ---------- */
const GENDER_OPTIONS = [
  { label: '男', value: 'male' },
  { label: '女', value: 'female' },
  { label: '其他', value: 'other' },
  { label: '不愿透露', value: 'prefer-not-to-say' }
]

const ROLE_OPTIONS = [
  { label: '初中生', value: 'student-junior-high' },
  { label: '高中生', value: 'student-senior-high' },
  { label: '本科生', value: 'student-undergrad' },
  { label: '硕士生', value: 'student-grad' },
  { label: '博士生', value: 'student-phd' },
  { label: '在职', value: 'employed' },
  { label: '自由职业', value: 'freelancer' },
  { label: '创业者', value: 'entrepreneur' },
  { label: '家长', value: 'parent' },
  { label: '求职中', value: 'job-seeker' }
]

const PURPOSE_OPTIONS = [
  { label: '职业规划', value: 'career-planning' },
  { label: '学习方向', value: 'study-direction' },
  { label: '留学规划', value: 'study-abroad-planning' },
  { label: '考研深造', value: 'graduate-school-planning' },
  { label: '自我探索', value: 'self-exploration' },
  { label: '人际洞察', value: 'relationship-insight' },
  { label: '领导力成长', value: 'leadership-growth' },
  { label: '创业适配', value: 'entrepreneur-fit' },
  { label: '学业减压', value: 'academic-stress-relief' },
  { label: '了解孩子', value: 'parent-understanding-child' }
]

const STATE_OPTIONS = [
  { label: '稳定期', value: 'stable' },
  { label: '过渡期', value: 'transition' },
  { label: '压力期', value: 'stress' },
  { label: '迷茫期', value: 'stuck' },
  { label: '成长期', value: 'growth-seeking' }
]

const HORIZON_OPTIONS = [
  { label: '即刻', value: 'immediate' },
  { label: '1 年内', value: 'within-1-year' },
  { label: '1-3 年', value: '1-3-years' },
  { label: '3 年以上', value: '3-plus-years' }
]

module.exports = {
  CATEGORY_LABELS,
  SCALE_LABELS,
  ENNEAGRAM_NAMES,
  ENNEAGRAM_DESC,
  MBTI_DESC,
  HOLLAND_NAMES,
  HOLLAND_DESC,
  GALLUP_DOMAINS,
  GALLUP_DOMAIN_DESC,
  GALLUP_THEMES,
  GENDER_OPTIONS,
  ROLE_OPTIONS,
  PURPOSE_OPTIONS,
  STATE_OPTIONS,
  HORIZON_OPTIONS
}
