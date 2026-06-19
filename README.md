# 旅图 Lv - AI 旅行规划平台

AI 驱动的全流程旅行规划平台，覆盖灵感发现、目的地推荐、行程规划、机位穿搭推荐、社区分享的完整旅行旅程。

## 功能概览

| 阶段 | 功能 | 说明 |
|------|------|------|
| 灵感 | AI 目的地推荐 | 根据季节/兴趣/预算智能推荐目的地 |
| 决策 | 方案对比 | 多维度对比旅行方案（出片指数/效率/花费） |
| 规划 | 行程编辑 | 拖拽排序、AI 调整、自动保存、版本快照 |
| 准备 | 机位 & 穿搭推荐 | 摄影机位推荐 + 穿搭搭配建议 |
| 执行 | 协同编辑 | WebSocket 实时协同 + 通知系统 |
| 分享 | 社区互动 | 发帖、评论、收藏、搜索 |

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL + SQLAlchemy (async) + Alembic 迁移
- **缓存**: Redis (可选，无 Redis 自动降级内存缓存)
- **鉴权**: JWT (HS256) + bcrypt + OAuth2
- **AI**: LLM/Agent 双模式 (无 Key 自动降级 Mock)
- **限流**: 滑动窗口 (auth 5/min, AI 10/min, post 20/min)
- **实时**: WebSocket 协同编辑 + SSE 异步任务推送

### 前端
- **框架**: React 18 + TypeScript + Vite
- **状态管理**: Zustand
- **路由**: React Router v6 (懒加载)
- **样式**: CSS Variables + 设计令牌系统
- **国际化**: i18n (中/英)
- **其他**: ErrorBoundary + Sentry + PWA + SEO

### DevOps
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx + SSL (Let's Encrypt)
- **CI/CD**: GitHub Actions
- **监控**: Prometheus 埋点

## 快速开始

### 前置要求
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ (或使用 Docker)
- Redis 7+ (可选)

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/Amory-ZDF/lvtu-AI.git
cd lvtu-AI

# 后端
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env       # 编辑 .env 配置
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 前端 (新终端)
cd frontend
npm install
cp .env.example .env
npm run dev
```

访问 http://localhost:5173 开始使用。

### Docker 部署

```bash
# 开发环境
docker compose up -d

# 生产环境 (含 SSL)
cp .env.example .env.production  # 编辑生产配置
bash deploy.sh
```

## 项目结构

```
lvtu-AI/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/          # API 路由 (REST + WebSocket)
│   │   ├── core/            # 配置、安全、异常、监控
│   │   ├── db/              # 数据库、缓存、Redis
│   │   ├── integrations/    # AI/LLM/Agent/RAG 集成
│   │   ├── middleware/      # 鉴权、限流、日志
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   └── services/        # 业务逻辑层
│   ├── alembic/             # 数据库迁移
│   └── tests/               # 测试 (94 个)
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── components/      # UI 组件
│   │   ├── hooks/           # 自定义 Hooks
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API 服务层
│   │   ├── store/           # Zustand 状态管理
│   │   └── types/           # TypeScript 类型定义
│   └── e2e/                 # Playwright E2E 测试
├── nginx/                    # Nginx 反向代理配置
├── docker-compose.yml        # 开发环境编排
├── docker-compose.prod.yml   # 生产环境编排
└── deploy.sh                 # 一键部署脚本
```

## 环境变量

复制 `.env.example` 并修改：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接 | SQLite (开发) / PostgreSQL (生产) |
| `JWT_SECRET_KEY` | JWT 签名密钥 | **必须修改** |
| `AI_PROVIDER` | AI 服务提供商 | mock |
| `AI_API_KEY` | AI API 密钥 | 空 (Mock 模式) |
| `RATE_LIMIT_ENABLED` | 限流开关 | true |
| `CORS_ALLOW_ORIGINS` | CORS 允许来源 | localhost |

## AI 模式

| 模式 | 说明 | 配置 |
|------|------|------|
| Mock | 返回预设数据，无需 API Key | `AI_PROVIDER=mock` |
| LLM | 调用真实大语言模型 | `AI_PROVIDER=openai` + `AI_API_KEY` |
| Agent | 多步骤 AI 工作流 | `AGENT_PROVIDER=openai` + `AGENT_API_KEY` |

## 测试

```bash
# 后端测试
cd backend
pytest                          # 全部测试 (94 个)
pytest tests/test_auth.py       # 鉴权测试

# 前端构建检查
cd frontend
npm run build

# E2E 测试
npx playwright install
npx playwright test
```

## License

MIT
