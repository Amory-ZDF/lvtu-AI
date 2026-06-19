# Lv Backend Foundation

基于 FastAPI + PostgreSQL + SQLAlchemy + Alembic 的后端基础工程。

## 目录结构

```text
backend/
|- app/
|  |- api/
|  |- core/
|  |- db/
|  |- integrations/
|  |- middleware/
|  |- models/
|  |- repositories/
|  |- schemas/
|  |- services/
|  `- main.py
|- alembic/
|- tests/
|- .env.example
|- alembic.ini
`- pyproject.toml
```

## 本地运行

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

健康检查：
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`

规划占位接口：
- `POST /api/v1/planning/destinations`
- `POST /api/v1/planning/routes`
- `POST /api/v1/planning/media/placeholders`

## 响应约定

- 成功响应统一为 `success/data/meta`
- 错误响应统一为 `success/error/meta`
- `meta` 包含 `request_id`、`timestamp`，占位接口额外返回 `provider`
- 全局校验异常和未捕获异常已统一转换为标准错误结构

示例成功响应：

```json
{
  "success": true,
  "data": {},
  "meta": {
    "request_id": "3dcf1f3f-df46-4bb0-9c35-639a3ac22a7b",
    "timestamp": "2026-06-17T11:30:00Z",
    "provider": "mock",
    "warnings": []
  }
}
```

示例错误响应：

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "请求参数校验失败",
    "details": [
      {
        "field": "body.duration_days",
        "message": "Input should be greater than or equal to 1"
      }
    ]
  },
  "meta": {
    "request_id": "3dcf1f3f-df46-4bb0-9c35-639a3ac22a7b",
    "timestamp": "2026-06-17T11:31:00Z",
    "provider": null,
    "warnings": []
  }
}
```

## 最小验证

```bash
cd backend
source .venv/bin/activate
ruff check .
pytest
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 部署准备

- 通过环境变量读取应用、数据库、AI Provider、Agent Provider、媒体 Provider 配置
- 入口命令可直接用于容器或 PaaS：`uvicorn app.main:app --host 0.0.0.0 --port 8000`
- 若在容器中部署，启动前执行 `alembic upgrade head`
- 当前 AI / Agent / 图片资源均为可替换 mock integration，不依赖真实密钥即可启动
- 已启用请求 ID、中间件访问日志和 CORS，便于前后端联调与基础观测

## 设计说明

- 使用 `pydantic-settings` 统一读取环境变量。
- 使用 `SQLAlchemy 2.x` 管理 ORM 和数据库会话。
- 使用 `Alembic` 管理 schema 迁移。
- `integrations/` 保留 AI、Agent 和媒体资源提供方的替换入口。
- 当前不接入任何真实 AI、Agent 或私有密钥。
