/**
 * config.js — 全局配置
 *
 * 云托管模式（推荐）：
 *  - 填入 CLOUD_ENV（云开发环境ID）后自动走 wx.cloud.callContainer()
 *  - 无需域名备案、无需SSL证书、无需配置服务器域名白名单
 *
 * 传统模式（备用）：
 *  - CLOUD_ENV 留空，走 wx.request() + BASE_URL
 *  - 需 HTTPS + 已备案域名 + 服务器域名白名单
 */
module.exports = {
  // === 云托管配置 ===
  // 云开发环境ID（在开发者工具→云开发→设置 里查看）
  CLOUD_ENV: 'xingyaoqicheng-d4gqkp52ef36b32dc',
  // 云托管服务名（与 container.config.json 中 containerName 一致）
  CLOUD_SERVICE: 'personality-api',

  // === 传统模式配置（CLOUD_ENV 为空时使用） ===
  // 后端 API 地址（HTTPS + 域名）
  BASE_URL: 'https://api.xingyaoqicheng.cn',

  // true = 前端独立 mock（后端未启动时用）；false = 直连后端
  USE_MOCK: false,

  TOTAL_QUESTIONS: 120,

  PRICE_CN: '29.9',
  PRICE_ORIGINAL_CN: '49.9',
  PRICE_FEN: 2990,

  // 支付成功后轮询报告生成状态
  POLL_INTERVAL_MS: 3000,
  POLL_MAX_COUNT: 40
}
