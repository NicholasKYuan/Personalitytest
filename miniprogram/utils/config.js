/**
 * config.js — 全局配置
 *
 * 开发期：
 *  - BASE_URL 指向本地后端，微信开发者工具需勾选「不校验合法域名」。
 *  - 后端未启动时可把 USE_MOCK 置为 true，前端用内置 mock 数据独立预览完整流程。
 */
module.exports = {
  // 后端 API 地址（权威定义见 BACKEND_SPEC.md §4）
  BASE_URL: 'http://127.0.0.1:8000',

  // true = 前端独立 mock（后端未启动时用）；false = 直连后端
  USE_MOCK: true,

  TOTAL_QUESTIONS: 120,

  PRICE_CN: '29.9',
  PRICE_ORIGINAL_CN: '49.9',
  PRICE_FEN: 2990,

  // 支付成功后轮询报告生成状态
  POLL_INTERVAL_MS: 3000,
  POLL_MAX_COUNT: 40
}
