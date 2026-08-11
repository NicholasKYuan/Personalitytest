# 星耀启程 · 人格测评

融合 **九型人格 · MBTI · 霍兰德 · 盖洛普** 四体系的人格测评 Web 应用。

## 功能特性

- **1500 题融合题库**：每道题同时映射 1-4 个测评体系，支持 forced-choice 和 likert-4 两种量表
- **智能筛选器**：根据用户画像（年龄/角色/目的/状态）动态筛选 120 题，保证体系覆盖与类别均衡
- **四体系评分**：九型人格 9 型、MBTI 8 维、霍兰德 6 型、盖洛普 4 领域同步计算
- **AI 深度分析**：集成 Minimax M3，生成 9000+ 字个性化深度解读报告
- **可下载报告**：品牌化 HTML 报告，含雷达图、柱状图、Markdown 排版

## 技术栈

- **后端**：FastAPI + Uvicorn
- **前端**：原生 HTML / CSS / JavaScript（无框架依赖）
- **AI**：Minimax M3（OpenAI 兼容 API）
- **题库**：JSONL 格式，1500 题

## 项目结构

```
├── question-bank/        # 题库
│   ├── items.jsonl        # 1500 题主文件
│   ├── schema.json        # 题目 schema
│   ├── taxonomy.md        # 四体系分类体系
│   └── catalog/           # 数字资产目录
├── selector/             # 筛选器
│   ├── selector.py        # 筛选逻辑
│   ├── scorer.py          # 四体系评分
│   └── profile-schema.json
├── webapp/               # Web 应用
│   ├── backend/           # FastAPI 后端
│   │   ├── app.py         # 主应用
│   │   ├── ai_analyzer.py # AI 深度分析
│   │   ├── scorer.py      # 评分引擎
│   │   └── report_generator.py
│   ├── frontend/          # 前端
│   │   ├── index.html
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── templates/         # 报告模板
└── skill/                # Skill 定义
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r webapp/backend/requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 MINIMAX_API_KEY
```

### 3. 启动服务器

```bash
cd webapp/backend
uvicorn app:app --reload --port 8000
```

### 4. 访问应用

浏览器打开 http://127.0.0.1:8000

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/session` | 创建会话，返回 120 题 |
| POST | `/api/submit` | 提交答案，返回评分结果 |
| POST | `/api/analyze` | AI 深度分析（需先提交答案） |
| GET | `/api/report/{session_id}` | 下载 HTML 报告 |
| GET | `/api/health` | 健康检查 |

## License

MIT
