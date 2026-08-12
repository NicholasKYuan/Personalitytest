# 星耀启程人格测评 · 微信小程序后端技术方案（BACKEND_SPEC）

> 版本：v1.0　作者：be-dev　日期：2026-08-12
> 适用范围：小程序前端开发（Task #5）、支付集成（Task #3）、端到端测试（Task #4）

---

## 0. 现状盘点（现有代码阅读结论）

| 组件 | 位置 | 说明 |
|------|------|------|
| FastAPI 入口 | `webapp/backend/app.py`（注意不是 main.py） | 提供 session/submit/analyze/report 四接口 + 静态前端 |
| 选题器 | `selector/selector.py` | `select(profile, bank)` 从 2000 题库按画像筛 **120 题**，含维度覆盖校验与去重 |
| 评分器 | `webapp/backend/scorer.py` | `score_answers()` 计算四体系结果；`generate_free_summary()` 生成免费简评 |
| AI 分析 | `webapp/backend/ai_analyzer.py` | 调用 Minimax M3（OpenAI 兼容），`max_tokens=8000`，**单次 30~90s**，含禁用词/英文过滤 |
| 报告生成 | `webapp/backend/report_generator.py` | 填充 HTML 模板（仅 Web 端用） |
| 题库 | `question-bank/items.jsonl` | 2000 题，约 1.4MB，JSONL 格式 |
| 会话存储 | `webapp/backend/sessions/*.json` | 当前为 JSON 文件，**无 openid 关联、无支付状态** |

### 现有接口（Web 端）
```
POST /api/session          创建会话 → 返回 120 题（已剥除 score）
POST /api/submit           提交答案 → 返回四体系结果 + free_summary
POST /api/analyze          调用 Minimax 生成 AI 深度解读（当前免费开放）
GET  /api/report/{id}      下载 HTML 报告
GET  /api/health
```

**与小程序需求的差距**：① 无微信登录/openid 关联；② analyze 接口无支付门槛；③ 会话存 JSON 文件不可靠；④ AI 分析同步阻塞，小程序侧 UX 不可接受；⑤ 无微信支付 v3 集成。

---

## 1. 方案评估：A 复用 FastAPI vs B 微信云开发

### 方案 A：复用 FastAPI + 公网云服务器 + HTTPS 域名

| 维度 | 评价 |
|------|------|
| 复用程度 | **几乎零重写**。选题/评分/AI 分析/报告模板全部现成且已测试 |
| AI 长耗时 | **优**。长驻服务上用「支付回调 → 后台异步生成 → 前端轮询」模式，无超时压力 |
| 支付回调 | **优**。微信支付 v3 回调要求公网 HTTPS URL，自管服务器完全可控，验签/幂等/对账可精细实现 |
| 开发成本 | 低。主要是新增登录/支付/订单/异步任务模块（约 500~800 行） |
| 运维成本 | 中。需部署、进程守护、日志、备份；轻量服务器约 ¥60/月 |
| 硬性前提 | 域名 + ICP 备案（**备案 1~2 周是主要时间成本**，须尽早启动）+ HTTPS 证书 |

### 方案 B：微信小程序云开发（云函数 + 云数据库）

| 维度 | 评价 |
|------|------|
| 基础设施 | 免域名免备案免服务器，云数据库/云存储内置，openid 天然可得 |
| AI 长耗时 | **致命短板**。云函数 HTTP/小程序调用默认 **60s 超时**，MiniMax M3 8000 token 大概率超时；需改造为「触发型云函数 + 定时器」异步链路，复杂度与不确定性高 |
| 代码迁移 | **高成本高风险**。selector.py（约 420 行筛选算法）、scorer、ai_analyzer 需从 Python 移植到 Node.js 云函数，且 2000 题需导入云数据库或打包云存储 |
| 支付回调 | 云开发对微信支付 v3 回调不友好：普通云函数**没有公网回调地址**，需借云托管/API 网关（仍要域名），与「免域名」优势冲突 |
| 成本 | 免费额度有限，调用量上来后按量计费，未必比轻量服务器便宜 |
| 结论 | 适合「无存量代码、逻辑简单」的新项目；对本项目**迁移成本 > 收益** |

### 推荐结论：**方案 A（复用 FastAPI 后端 + 云服务器 + HTTPS）**

核心理由：
1. **复用已测试代码**，开发成本最低、风险最低；
2. **AI 长耗时分析只有长驻服务器能优雅支持**（异步任务 + 轮询，且后续可换队列/加缓存）；
3. **支付回调需要可控的 HTTPS 端点**，这是方案 A 的硬优势；
4. 小程序上线本就强制 HTTPS + 备案域名，反正都要准备，方案 A 边际成本低；
5. Web 端与小程序共享一套后端，产品迭代一致。

### 折中备选：腾讯云 CloudBase 云托管
若团队实在不想自管服务器，可把现有 FastAPI 打包为 **Docker 镜像** 部署到 CloudBase 云托管（HTTP 访问服务，同样需绑定域名）。**建议后端代码从一开始就按可容器化方式编写**（配置走环境变量、日志走 stdout），保留这条平滑迁移路径，但首期仍以自管轻量服务器为默认。

---

## 2. 总体架构

```
┌──────────────┐    HTTPS+JSON     ┌──────────────────────────────────────┐
│  微信小程序   │ ────────────────▶ │  公网云服务器（轻量 2C2G，Linux）      │
│  (AppID:     │    wx.request     │  ┌────────────────────────────────┐  │
│  wx7a0e…2f84)│                   │  │ nginx (HTTPS 终结/反代)          │  │
│              │                   │  │   └─▶ uvicorn: FastAPI (Python) │  │
└──────────────┘                   │  │        ├ /api/login  (code2session)│ │
        │  wx.login/code           │  │        ├ /api/session|submit      │ │
        ▼                          │  │        ├ /api/report/order|detail  │ │
┌──────────────┐                   │  │        ├ /api/pay/notify (回调)    │ │
│  微信服务器   │◀─ 支付回调(HTTPS)─│  │        └ 后台异步任务(线程池)        │ │
│  code2session│                   │  ├── SQLite(初期)/MySQL(上线)         │ │
│  微信支付 v3 │                   │  ├── question-bank/items.jsonl       │ │
└──────────────┘                   │  └── 环境变量(.env)                  │ │
      ▲                           └──────────────────────────────────────┘
      └────────────── MiniMax M3 API（AI 深度分析，外部调用）
```

**关键设计原则**
- 一切业务接口以 **token** 鉴权（openid 从服务端换取，不信任前端）。
- **AI 分析不在请求里同步等**：支付成功后由后台异步生成，前端轮询状态，天然规避 60s+ 延迟。
- **金额由服务端写死 2990 分**，前端不可传价。
- 报告内容（AI 章节）**只**通过 `POST /api/report/detail` 在订单 paid 后下发，免费接口不返回任何 AI 内容。

---

## 3. 微信登录与鉴权

### POST /api/login
小程序端先 `wx.login()` 取 code，再调本接口。

请求：
```json
{
  "code": "wx.login() 返回的临时 code",
  "nickname": "可选昵称",
  "avatar_url": "可选头像"
}
```

服务端逻辑：
1. 用 `code` + AppID/AppSecret 调微信 `code2session` → `{openid, session_key}`；
2. `users` 表 upsert（openid 维度）；
3. 生成随机 token（`secrets.token_urlsafe(32)`）写入 `users.token`，有效期 7 天；
4. 返回 token。

响应：
```json
{
  "code": 0,
  "data": {
    "token": "8bA9…",
    "openid": "oXXXXXXXXXXXX",
    "is_new": true,
    "expires_in": 604800
  }
}
```

> 鉴权方式：后续所有业务接口请求头 `Authorization: Bearer <token>`。服务端中间件查 `users.token` 得 openid；token 不存在/过期返回 `401`。
> 采用 DB 存储的 opaque token（而非 JWT）：可主动吊销、无需新增依赖，对小程序场景足够。

### 错误码约定
统一响应包装：
```json
{ "code": 0, "message": "ok", "data": {...} }
```
| code | 含义 |
|------|------|
| 0 | 成功 |
| 401 | 未登录/token 失效 |
| 403 | 已登录但无权限（未支付等） |
| 404 | 会话/订单不存在 |
| 400 | 参数错误 |
| 500 | 服务端错误 |
| 1001 | 会话不属于当前用户 |
| 1002 | 订单已存在/状态冲突 |
| 2001 | 报告生成中（前端应轮询 status） |
| 2002 | AI 生成失败（已降级模板，仍可看报告） |

---

## 4. API 接口定义（小程序前端契约）

> 统一前缀 `/api`，base URL 由环境配置（开发期可指向本地 + 开发者工具「不校验合法域名」）。

### 4.1 POST /api/session — 创建测试会话

请求：
```json
{
  "profile": {
    "name": "小明",
    "age": 22,
    "gender": "male",
    "role": "student-undergrad",
    "purpose": "career-planning",
    "current_state": "transition",
    "decision_horizon": "1-3-years",
    "birth_date": "2004-03-15"
  }
}
```
`age`/`role`/`purpose` 必填，其余可选（枚举与 `selector/profile-schema.json` 一致）。

服务端逻辑：校验参数 → `selector.select(profile, BANK)` 出 120 题 → 生成 `session_id`（uuid4）→ 完整题（含 score）与 profile 存库 → 返回剥除 score 的题目。

响应：
```json
{
  "code": 0,
  "data": {
    "session_id": "uuid",
    "total": 120,
    "questions": [
      {
        "id": "Q0001",
        "stem": "聚会中认识新朋友，我更倾向于",
        "scale": "forced-choice",
        "options": [ { "text": "主动找话题，让场面热闹起来" }, { "text": "…" } ],
        "category": "interpersonal-relationship",
        "difficulty": 2
      }
    ]
  }
}
```
> **重要**：`options` 只返回 `text`，绝不返回 `score`（防前端扒分数）。

### 4.2 POST /api/submit — 提交答案，返回免费结果

请求：
```json
{
  "session_id": "uuid",
  "answers": [
    { "question_id": "Q0001", "option_index": 0 },
    { "question_id": "Q0002", "option_index": 2 }
  ]
}
```

服务端逻辑：校验 session 属于当前用户 → 校验答案数 ≥ 120 → `score_answers()` 评分 → `generate_free_summary()` → 结果与答案落库 → 会话 status 置 `answered`。

响应：
```json
{
  "code": 0,
  "data": {
    "session_id": "uuid",
    "results": {
      "enneagram": { "main_type": 3, "type_name": "成就者", "scores": { "type1": 12, "…": 0 } },
      "mbti": { "type": "ENTJ", "dimensions": { "E": 15, "I": 5, "S": 8, "N": 12, "T": 18, "F": 2, "J": 14, "P": 6 } },
      "holland": { "code": "EAS", "scores": { "R": 5, "I": 8, "A": 12, "S": 10, "E": 15, "C": 7 } },
      "gallup": { "top_domain": "executing", "domains": { "executing": 20, "influencing": 12, "relationship_building": 8, "strategic_thinking": 15 }, "top_themes": ["achiever", "arranger", "focus"] }
    },
    "free_summary": "小明的九型人格主型为【3号 - 成就者】。…解锁深度报告，获取四体系交叉解读…",
    "detailed_available": true,
    "paid": false
  }
}
```

### 4.3 POST /api/report/order — 创建付费订单（29.9 元）

请求：
```json
{ "session_id": "uuid" }
```

服务端逻辑：
1. 校验 session 属于当前用户且已 `answered`；
2. **幂等**：查 `orders` 表，若该 session 已有 `pending/paid` 订单直接复用（已 paid 则直接返回已购状态）；
3. 生成 `out_trade_no`（如 `SX` + 时间戳 + 随机串，≤32 位）；
4. 调微信支付 v3 统一下单（JSAPI）：
   - `appid=wx7a0e273595082f84`，`mchid=商户号`，`description=星耀启程人格测评深度报告`，
   - `amount.total=2990`（**分**），`notify_url=https://<域名>/api/pay/notify`，
   - `payer.openid=当前用户 openid`；
5. 用返回的 `prepay_id` 生成 JSAPI 调起参数并签名；
6. 订单落库（status=`pending`）。

响应：
```json
{
  "code": 0,
  "data": {
    "order_id": 10001,
    "out_trade_no": "SX1720000000123abc",
    "pay_params": {
      "appId": "wx7a0e273595082f84",
      "timeStamp": "1720000000",
      "nonceStr": "xxxx",
      "package": "prepay_id=wx123456789",
      "signType": "RSA",
      "paySign": "Base64(RSA-SHA256 签名)"
    },
    "amount_fen": 2990
  }
}
```
小程序端拿到 `pay_params` 直接调 `wx.requestPayment(pay_params)`。

### 4.4 POST /api/pay/notify — 微信支付回调（**小程序不直接调用**）

微信支付 v3 在支付成功后会主动 POST 到此 URL，要求服务端在 5 秒内应答。

服务端逻辑：
1. **验签**：用微信支付平台证书校验请求头 `Wechatpay-Signature`；
2. **解密**：AES-256-GCM 解密 body，得到 `{out_trade_no, transaction_id, trade_state, amount:{total}, …}`；
3. 校验 `amount.total == 2990` 且订单为 `pending` → 置 `paid`，记 `transaction_id/paid_at`；
4. **幂等**：重复回调（微信最多重试 15 天）时，若已 paid 直接返回成功，不重复扣 AI 费用；
5. 触发 **异步 AI 分析任务**（见 §6）；
6. 返回 `{"code":"SUCCESS","message":"成功"}`（HTTP 200）。

### 4.5 GET /api/report/status?session_id=xxx — 查询状态

响应：
```json
{
  "code": 0,
  "data": {
    "payment_status": "paid",     // unpaid | pending | paid | closed
    "report_status": "ready",     // none | generating | ready | failed
    "paid": true,
    "is_ready": true
  }
}
```
- 支付前调用：`payment_status=unpaid`；
- 支付成功后后台开始生成：`report_status=generating`；
- 生成完成：`report_status=ready`；
- AI 失败已降级：`report_status=failed`（报告仍可看模板版）。
- 前端策略：支付成功后每 **3~5s** 轮询，`is_ready=true` 后跳转报告页。

### 4.6 POST /api/report/detail — 支付成功后获取完整报告

请求：
```json
{ "session_id": "uuid" }
```

服务端逻辑：
1. 校验 session 属于当前用户；
2. 查订单：未支付 → `403 / code=403`；paid 但 `generating` → `code=2001`（前端继续轮询）；
3. 已 paid 且 ready/failed → 返回完整报告（JSON 结构化，**小程序端用 markdown 渲染**，如 towxml / mp-html 插件）。

响应：
```json
{
  "code": 0,
  "data": {
    "session_id": "uuid",
    "report": {
      "profile": { "name": "小明", "age": 22, "role": "student-undergrad", "purpose": "career-planning" },
      "results": { "enneagram": {…}, "mbti": {…}, "holland": {…}, "gallup": {…} },
      "sections": [
        { "title": "九型人格深度解读", "content": "## …\n- …（markdown）" },
        { "title": "MBTI深度分析", "content": "…" },
        { "title": "霍兰德职业方向", "content": "…" },
        { "title": "盖洛普优势发挥", "content": "…" },
        { "title": "四体系综合交叉解读", "content": "…" },
        { "title": "传统易学结合解读", "content": "…" }   // 仅当填了 birth_date
      ],
      "generated_at": "2026-08-12 10:00:00",
      "fallback_used": false
    }
  }
}
```

### 4.7 GET /api/health — 健康检查
```json
{ "code": 0, "data": { "status": "ok", "bank_size": 2000 } }
```

---

## 5. 数据存储设计

**初期 SQLite（单文件零运维）→ 上线 MySQL（推荐 5.7+，utf8mb4）。** 统一用 SQLAlchemy 封装，切换成本低。JSON 字段存 TEXT（MySQL 用 JSON 类型亦可）。

### users（用户表）
| 字段 | 类型 | 说明 |
|------|------|------|
| openid | VARCHAR(64) PK | 微信 openid |
| nickname | VARCHAR(64) | 昵称 |
| avatar_url | VARCHAR(512) | 头像 |
| token | VARCHAR(128) | 当前登录 token（可空） |
| token_expire_at | DATETIME | token 过期时间 |
| created_at / last_login_at | DATETIME | 时间戳 |

### sessions（测试会话/答题记录）
| 字段 | 类型 | 说明 |
|------|------|------|
| session_id | VARCHAR(36) PK | uuid4 |
| openid | VARCHAR(64) INDEX | 归属用户 |
| profile | TEXT(JSON) | 用户画像 |
| questions | TEXT(JSON) | 完整 120 题（含 score，仅服务端） |
| answers | TEXT(JSON) NULL | 已提交答案 |
| results | TEXT(JSON) NULL | 四体系评分结果 |
| free_summary | TEXT NULL | 免费简评 |
| status | VARCHAR(16) | `created → answered → generating → ready / failed` |
| ai_sections | TEXT(JSON) NULL | AI 章节（付费内容，服务端保护） |
| created_at / updated_at | DATETIME | 时间戳 |

### orders（订单表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT AUTO PK | 自增 |
| out_trade_no | VARCHAR(32) UNIQUE | 商户订单号 |
| session_id | VARCHAR(36) INDEX | 关联会话 |
| openid | VARCHAR(64) INDEX | 支付人 |
| amount_fen | INT | 固定 2990 |
| status | VARCHAR(16) | `pending / paid / closed / refunded` |
| prepay_id | VARCHAR(64) | 微信预支付单号 |
| transaction_id | VARCHAR(64) | 支付成功后微信交易号 |
| notify_raw | TEXT(JSON) | 回调原始数据（对账用） |
| created_at / paid_at | DATETIME | 时间戳 |

### 索引建议
- `sessions(openid, status)`；`orders(openid, status)`；`orders(session_id)`。

### 免费 vs 付费控制（服务端强制）
1. `submit` 只返回 `results + free_summary`——**不包含任何 AI 内容**；
2. `ai_sections`（付费正文）**只**在 `report/detail` 且订单 `paid` 后下发；
3. `status` 接口只返回状态位，不透传内容；
4. 全部接口校验 session 归属（`sessions.openid == token.openid`），防跨用户白嫖；
5. 金额写死 2990 分，回调校验 `amount.total` 与订单一致。

---

## 6. AI 深度分析异步化设计（重点）

现状 `ai_analyzer.generate_detailed_analysis()` 同步调用 MiniMax M3（max_tokens=8000），**单次 30~90s**，不能放在请求线程里。

**方案：支付成功回调 → 后台异步生成 → 轮询取结果**

```
支付回调(paid)
   │
   ▼
提交后台任务（FastAPI BackgroundTasks 或线程池，进程内简单队列）
   │
   ├─ generate_detailed_analysis(results, profile)
   │     ├─ 成功 → 写 sessions.ai_sections, status=ready
   │     └─ 失败(超时/网络) → 重试2次(指数退避) → 仍失败 → status=failed，写日志
   │
   └─ 前端 GET /api/report/status 轮询（3~5s/次）
```

要点：
- **生成时机**：支付成功后，而非答题后（避免为未付费用户白付 AI 成本）。
- **降级兜底**：`status=failed` 时，`report/detail` 返回规则化模板报告（`report_generator` 以内置内容代替 AI 章节），**保证付费用户一定有报告可看**，`fallback_used=true`。
- **防并发**：同一 session 只允许一个生成任务（DB 行锁/`generating` 状态判断），回调重试不会重复触发。
- **容量**：进程内线程池即可满足冷启动阶段（并发 < 20）；后续量大再换 Celery/RQ 或独立 worker 进程，接口契约不变。
- **幂等成本**：AI 章节生成后落库缓存，重复请求不重复调用。

---

## 7. 部署与运维要求

### 7.1 服务器
- 腾讯云/阿里云轻量应用服务器，2C2G，Ubuntu 22.04（约 ¥60/月；首年常有折扣）。
- 进程：`uvicorn app:app --host 127.0.0.1 --port 8000`，systemd 守护。
- nginx 反代 + HTTPS 终结（`server_name api.<域名>`，`proxy_pass http://127.0.0.1:8000`，`client_max_body_size 2m`）。

### 7.2 域名与备案（关键前置，需尽早启动）
- 小程序上线**强制**要求 request 合法域名为 **HTTPS + 已备案**域名。
- ICP 备案：1~2 周，**应立即并行启动**；备案主体需与小程序主体一致。
- HTTPS 证书：云厂商免费 DV 证书（或 Let's Encrypt），nginx 配置。

### 7.3 小程序后台配置
- 「开发管理 → 服务器域名 → request 合法域名」：`https://api.<域名>`。
- 开发调试期：微信开发者工具勾选「不校验合法域名」，可直连本地/公网 IP。

### 7.4 环境变量清单（`.env`）
```
# AI
MINIMAX_API_KEY=...
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
MINIMAX_MODEL=MiniMax-M3

# 微信小程序
WX_APPID=wx7a0e273595082f84
WX_SECRET=...

# 微信支付 v3
MCH_ID=...
MCH_SERIAL_NO=...                    # 商户 API 证书序列号
MCH_PRIVATE_KEY_PATH=./certs/apiclient_key.pem
WXPAY_API_V3_KEY=...                  # 32 位 APIv3 密钥（AES 解密用）
WXPAY_PLATFORM_CERT_PATH=./certs/platform_cert.pem   # 验签/解密用平台证书
WXPAY_NOTIFY_URL=https://api.<域名>/api/pay/notify

# 存储
DATABASE_URL=sqlite:///./app.db        # 或 mysql+pymysql://user:pass@host/db
```

---

## 8. 需要团队提供的凭证清单（阻塞项，请 PM 跟进）

1. 小程序 **AppSecret**（AppID `wx7a0e273595082f84` 已有，Secret 需在小程序后台获取）；
2. 微信支付商户号 **mchid** + **APIv3 密钥** + **商户 API 证书**（apiclient_cert.pem / apiclient_key.pem）+ **证书序列号 serial_no**；
3. 微信支付 **平台证书**（验签解密用，可用「平台证书获取」API 或自动更新程序）；
4. 域名（待备案）+ 服务器购买。

---

## 9. 风险与注意事项

1. **测试号限制**：当前是微信**测试号**，测试号一般**无法绑定真实微信支付商户号**、无法上架。真实支付必须使用已注册并通过认证的小程序账号（个体工商户/企业主体）。开发阶段可用「模拟支付成功」开关（`PAY_MOCK=1` 时 `/api/pay/notify` 由测试接口触发）联调全流程，上线前切换真实支付。
2. **备案周期**：约 1~2 周，是整体上线的最长阻塞项，务必第一时间启动。
3. **支付回调可靠性**：回调接口必须幂等、5s 内应答、全程 try/except（任何异常都先记日志并返回失败，让微信重试）；订单状态以回调为准。
4. **AI 成本**：按生成次数计费，仅在支付成功后触发；需监控每日调用量。
5. **题库泄漏**：`options.score` 严禁下发到前端；AI 章节仅在付费接口下发。
6. **报告渲染**：小程序端展示 markdown 需引入渲染库（towxml / mp-html），前端需在 `report/detail` 的 `sections[].content` 上渲染。

---

## 10. 后端开发任务拆解（供 Task #3 等使用）

- [ ] T1 认证模块：`/api/login`（code2session）+ token 中间件 + users 表
- [ ] T2 会话模块改造：`/api/session`、`/api/submit` 接入鉴权、归属校验、SQLite 落库（替代 JSON 文件）
- [ ] T3 支付模块：微信支付 v3 下单 + JSAPI 签名 + `/api/pay/notify` 验签/解密/幂等 + orders 表
- [ ] T4 AI 异步生成：支付回调触发后台任务 + 重试/降级 + `/api/report/status`
- [ ] T5 `/api/report/detail`：付费校验 + 报告下发（AI 或降级模板）
- [ ] T6 部署：nginx + HTTPS + systemd + 环境变量（真实域名就绪后执行）
- [ ] T7 模拟支付开关 + 端到端联调（配合 Task #4）

**接口时序（前后端联调参考）**
```
login → session(取120题) → 答题 → submit(免费结果页)
      → 点击解锁 → report/order → wx.requestPayment
      → 支付成功 → 轮询 report/status → ready → report/detail(报告页)
```
