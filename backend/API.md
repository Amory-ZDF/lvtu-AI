# 旅图后端接口文档

本文档基于当前仓库中的 FastAPI 实现整理，覆盖已落地的非 AI 业务接口、健康检查接口，以及 AI/媒体占位接口。

当前代码来源：
- `backend/app/main.py`
- `backend/app/api/router.py`
- `backend/app/api/v1/health.py`
- `backend/app/api/v1/core_business.py`
- `backend/app/api/v1/planning.py`

## 1. 基础信息

- 服务名称：`Lv Backend`
- 默认版本：`v1`
- Base URL：`/api/v1`
- 在线文档：
  - Swagger UI：`/docs`
  - ReDoc：`/redoc`
- 鉴权现状：当前版本 **未接入登录鉴权**
- ID 类型：核心资源使用 `UUID`
- 数据库：`PostgreSQL`

## 2. 当前响应约定

当前后端存在两种响应风格，这一点前后端联调时需要特别注意。

### 2.1 统一包裹响应

以下接口使用统一响应结构：
- `GET /`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `POST /api/v1/planning/destinations`
- `POST /api/v1/planning/routes`
- `POST /api/v1/planning/media/placeholders`

成功响应格式：

```json
{
  "success": true,
  "data": {},
  "meta": {
    "request_id": "req_xxx",
    "timestamp": "2026-06-17T10:00:00Z",
    "provider": "mock",
    "warnings": []
  }
}
```

错误响应格式：

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "请求参数校验失败",
    "details": [
      {
        "field": "duration_days",
        "message": "Input should be greater than or equal to 1"
      }
    ]
  },
  "meta": {
    "request_id": "req_xxx",
    "timestamp": "2026-06-17T10:00:00Z",
    "provider": null,
    "warnings": []
  }
}
```

### 2.2 资源直返响应

以下业务接口当前直接返回资源对象或资源列表，不带 `success/data/meta` 包裹：
- `/users/...`
- `/trips/...`
- `/trip-days/...`
- `/community-posts...`

删除接口返回：
- `204 No Content`

说明：
- 这属于当前实现现状
- 如果后续你希望前后端接口完全统一，我可以再帮你做一次“响应结构收口”

## 3. 资源模型摘要

### 3.1 用户档案 `UserProfile`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "alice",
  "display_name": "Alice",
  "avatar_url": "https://...",
  "bio": "旅行爱好者",
  "created_at": "2026-06-17T10:00:00Z",
  "updated_at": "2026-06-17T10:00:00Z",
  "preference": {
    "id": "uuid",
    "user_id": "uuid",
    "departure_city": "上海",
    "preferred_styles": ["citywalk", "photography"],
    "budget_level": "medium",
    "language": "zh-CN",
    "timezone": "Asia/Shanghai",
    "created_at": "2026-06-17T10:00:00Z",
    "updated_at": "2026-06-17T10:00:00Z"
  }
}
```

### 3.2 行程 `Trip`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "上海周末出片游",
  "destination_name": "上海",
  "start_date": "2026-07-01",
  "end_date": "2026-07-03",
  "status": "draft",
  "cover_image_url": "https://...",
  "notes": "偏爱拍照和咖啡馆",
  "created_at": "2026-06-17T10:00:00Z",
  "updated_at": "2026-06-17T10:00:00Z"
}
```

### 3.3 行程天 `TripDay`

```json
{
  "id": "uuid",
  "trip_id": "uuid",
  "day_index": 1,
  "date": "2026-07-01",
  "title": "外滩与武康路",
  "summary": "适合 citywalk 和拍照",
  "created_at": "2026-06-17T10:00:00Z",
  "updated_at": "2026-06-17T10:00:00Z"
}
```

### 3.4 行程点 `TripPoint`

```json
{
  "id": "uuid",
  "trip_day_id": "uuid",
  "name": "武康大楼",
  "point_type": "spot",
  "address": "上海徐汇区",
  "latitude": 31.2035,
  "longitude": 121.4376,
  "start_time": "10:00:00",
  "end_time": "11:30:00",
  "sort_order": 1,
  "notes": "上午光线更好",
  "image_url": "https://...",
  "created_at": "2026-06-17T10:00:00Z",
  "updated_at": "2026-06-17T10:00:00Z"
}
```

### 3.5 打包清单项 `PackingItem`

```json
{
  "id": "uuid",
  "trip_id": "uuid",
  "name": "防晒霜",
  "category": "护肤",
  "quantity": 1,
  "is_checked": false,
  "note": "SPF50+",
  "created_at": "2026-06-17T10:00:00Z",
  "updated_at": "2026-06-17T10:00:00Z"
}
```

### 3.6 社区帖子 `CommunityPost`

```json
{
  "id": "uuid",
  "author_user_id": "uuid",
  "title": "上海两天一夜出片路线",
  "content": "适合周末城市漫游",
  "cover_image_url": "https://...",
  "status": "published",
  "like_count": 0,
  "comment_count": 0,
  "published_at": "2026-06-17T10:00:00Z",
  "created_at": "2026-06-17T10:00:00Z",
  "updated_at": "2026-06-17T10:00:00Z"
}
```

## 4. 接口清单

### 4.1 Root

#### `GET /`

用途：
- 验证服务已启动
- 返回服务名称和环境信息

响应：

```json
{
  "success": true,
  "data": {
    "service": "Lv Backend",
    "environment": "development",
    "message": "Lv Backend is running"
  },
  "meta": {
    "request_id": "req_xxx",
    "timestamp": "2026-06-17T10:00:00Z",
    "provider": null,
    "warnings": []
  }
}
```

### 4.2 健康检查

#### `GET /api/v1/health/live`

用途：
- 存活检查
- 一般给负载均衡、容器探针使用

响应字段：
- `status`: 通常为 `ok`
- `service`: 服务名
- `environment`: 环境名
- `details.database`: 存活检查不主动探测数据库，通常为 `not_checked`

#### `GET /api/v1/health/ready`

用途：
- 就绪检查
- 会执行数据库探测

响应字段：
- `status`:
  - `ok`: 数据库可用
  - `degraded`: 应用启动成功，但数据库不可用
- `details.database`:
  - `ok`
  - `unavailable`

### 4.3 用户档案

#### `GET /api/v1/users/{user_id}/profile`

用途：
- 获取用户基础资料和偏好档案

路径参数：
- `user_id`: UUID

成功响应：
- `200 OK`
- 返回 `UserProfileRead`

失败响应：
- `404 Not Found`: 用户不存在

#### `PUT /api/v1/users/{user_id}/profile`

用途：
- 创建或更新用户资料
- 首次可视为 upsert

路径参数：
- `user_id`: UUID

请求体：

```json
{
  "email": "user@example.com",
  "username": "alice",
  "display_name": "Alice",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "喜欢旅行和拍照",
  "departure_city": "上海",
  "preferred_styles": ["citywalk", "photography"],
  "budget_level": "medium",
  "language": "zh-CN",
  "timezone": "Asia/Shanghai"
}
```

成功响应：
- `200 OK`
- 返回 `UserProfileRead`

失败响应：
- `409 Conflict`: 用户邮箱或用户名冲突

### 4.4 行程管理

#### `GET /api/v1/users/{user_id}/trips`

用途：
- 获取指定用户的行程列表

排序规则：
- 按 `updated_at desc`
- 然后按 `created_at desc`

成功响应：
- `200 OK`
- 返回 `TripRead[]`

#### `POST /api/v1/users/{user_id}/trips`

用途：
- 创建行程

请求体：

```json
{
  "title": "上海周末出片游",
  "destination_name": "上海",
  "start_date": "2026-07-01",
  "end_date": "2026-07-03",
  "status": "draft",
  "cover_image_url": "https://example.com/cover.jpg",
  "notes": "偏爱拍照和咖啡馆"
}
```

成功响应：
- `201 Created`
- 返回 `TripRead`

失败响应：
- `404 Not Found`: 用户不存在
- `409 Conflict`: 行程创建失败

#### `GET /api/v1/users/{user_id}/trips/{trip_id}`

用途：
- 获取单个行程详情

成功响应：
- `200 OK`
- 返回 `TripRead`

失败响应：
- `404 Not Found`: 行程不存在

#### `PATCH /api/v1/users/{user_id}/trips/{trip_id}`

用途：
- 局部更新行程

请求体：
- `TripUpdate`
- 所有字段均可选

成功响应：
- `200 OK`
- 返回 `TripRead`

#### `DELETE /api/v1/users/{user_id}/trips/{trip_id}`

用途：
- 删除行程

成功响应：
- `204 No Content`

### 4.5 行程天

#### `GET /api/v1/trips/{trip_id}/days`

用途：
- 获取行程下的所有天

排序规则：
- 按 `day_index asc`

成功响应：
- `200 OK`
- 返回 `TripDayRead[]`

#### `POST /api/v1/trips/{trip_id}/days`

用途：
- 创建行程天
- 支持插入到指定顺序

请求体：

```json
{
  "day_index": 1,
  "date": "2026-07-01",
  "title": "第一天",
  "summary": "市区拍照与 citywalk"
}
```

说明：
- `day_index` 可省略
- 若传入，则服务端会重排所有天的顺序

成功响应：
- `201 Created`
- 返回 `TripDayRead`

#### `PATCH /api/v1/trips/{trip_id}/days/reorder`

用途：
- 整体重排行程天

请求体：

```json
{
  "ordered_ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

规则：
- 必须包含该行程的全部 `day_id`
- 不能重复

成功响应：
- `200 OK`
- 返回重排后的 `TripDayRead[]`

失败响应：
- `400 Bad Request`: 排序列表不完整或重复

#### `GET /api/v1/trips/{trip_id}/days/{day_id}`

用途：
- 获取单个行程天详情

#### `PATCH /api/v1/trips/{trip_id}/days/{day_id}`

用途：
- 更新单个行程天
- 可修改日期、标题、摘要
- 可调整 `day_index`

#### `DELETE /api/v1/trips/{trip_id}/days/{day_id}`

用途：
- 删除行程天
- 删除后自动重排剩余天序号

成功响应：
- `204 No Content`

### 4.6 行程点

#### `GET /api/v1/trip-days/{trip_day_id}/points`

用途：
- 获取某一天的所有行程点

排序规则：
- 按 `sort_order asc`

#### `POST /api/v1/trip-days/{trip_day_id}/points`

用途：
- 创建行程点
- 支持插入到指定顺序

请求体：

```json
{
  "name": "武康大楼",
  "point_type": "spot",
  "address": "上海徐汇区武康路",
  "latitude": 31.2035,
  "longitude": 121.4376,
  "start_time": "10:00:00",
  "end_time": "11:30:00",
  "sort_order": 1,
  "notes": "上午逆光较少，适合拍照",
  "image_url": "https://example.com/spot.jpg"
}
```

说明：
- `sort_order` 可选
- 若传入则自动进行顺序重排

#### `PATCH /api/v1/trip-days/{trip_day_id}/points/reorder`

用途：
- 整体重排行程点

请求体：

```json
{
  "ordered_ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

规则：
- 必须包含该天全部 `point_id`
- 不能重复

#### `GET /api/v1/trip-days/{trip_day_id}/points/{point_id}`

用途：
- 获取单个行程点详情

#### `PATCH /api/v1/trip-days/{trip_day_id}/points/{point_id}`

用途：
- 更新行程点内容
- 可修改基本信息
- 可调整 `sort_order`

#### `DELETE /api/v1/trip-days/{trip_day_id}/points/{point_id}`

用途：
- 删除行程点
- 删除后自动重排剩余点位顺序

成功响应：
- `204 No Content`

### 4.7 打包清单

#### `GET /api/v1/trips/{trip_id}/packing-items`

用途：
- 获取行程的打包清单

排序规则：
- 按 `created_at asc`
- 然后按 `id asc`

#### `POST /api/v1/trips/{trip_id}/packing-items`

用途：
- 新增打包清单项

请求体：

```json
{
  "name": "防晒霜",
  "category": "护肤",
  "quantity": 1,
  "is_checked": false,
  "note": "SPF50+"
}
```

#### `GET /api/v1/trips/{trip_id}/packing-items/{item_id}`

用途：
- 获取单个打包清单项

#### `PATCH /api/v1/trips/{trip_id}/packing-items/{item_id}`

用途：
- 更新打包清单项内容

请求体：
- `PackingItemUpdate`

#### `PATCH /api/v1/trips/{trip_id}/packing-items/{item_id}/checked`

用途：
- 单独更新勾选状态

请求体：

```json
{
  "is_checked": true
}
```

#### `DELETE /api/v1/trips/{trip_id}/packing-items/{item_id}`

用途：
- 删除打包清单项

成功响应：
- `204 No Content`

### 4.8 社区帖子

#### `GET /api/v1/community-posts`

用途：
- 获取社区帖子列表

查询参数：
- `author_user_id`: UUID，可选
- `status`: 字符串，可选
- `limit`: 默认 `20`，范围 `1-100`
- `offset`: 默认 `0`

排序规则：
- 按 `created_at desc`
- 然后按 `id desc`

#### `POST /api/v1/community-posts`

用途：
- 创建社区帖子

请求体：

```json
{
  "author_user_id": "uuid",
  "title": "上海两天一夜出片路线",
  "content": "适合周末出游和拍照",
  "cover_image_url": "https://example.com/cover.jpg",
  "status": "published",
  "published_at": "2026-06-17T10:00:00Z"
}
```

说明：
- 当 `status = published` 时，服务端会自动处理 `published_at`

#### `GET /api/v1/community-posts/{post_id}`

用途：
- 获取单篇帖子详情

#### `PATCH /api/v1/community-posts/{post_id}`

用途：
- 更新帖子

可更新字段：
- `author_user_id`
- `title`
- `content`
- `cover_image_url`
- `status`
- `published_at`
- `like_count`
- `comment_count`

#### `DELETE /api/v1/community-posts/{post_id}`

用途：
- 删除帖子

成功响应：
- `204 No Content`

### 4.9 规划占位接口

这组接口当前为占位实现，已预留出后续接入：
- 大模型 API
- Agent 编排
- 外部图片源
- 推荐/路线生成服务

#### `POST /api/v1/planning/destinations`

用途：
- 根据用户偏好返回候选目的地
- 当前返回 mock 结果，但结构已稳定

请求体：

```json
{
  "departure_city": "上海",
  "budget_min": 1000,
  "budget_max": 3000,
  "duration_days": 3,
  "season": "summer",
  "travel_style": ["citywalk", "photography"],
  "interests": ["咖啡馆", "拍照", "建筑"]
}
```

响应核心字段：
- `query_summary`
- `destinations[]`
  - `id`
  - `name`
  - `country_or_region`
  - `match_score`
  - `budget_range`
  - `best_season`
  - `vibe_tags`
  - `reasons`
  - `hero_image`
  - `gallery`

#### `POST /api/v1/planning/routes`

用途：
- 根据目的地生成路线方案
- 当前返回 mock 方案

请求体：

```json
{
  "destination_id": "shanghai-citywalk",
  "destination_name": "上海",
  "duration_days": 3,
  "pace": "balanced",
  "travelers": 2,
  "interests": ["拍照", "咖啡馆", "建筑"]
}
```

响应核心字段：
- `destination_name`
- `options[]`
  - `id`
  - `title`
  - `pace`
  - `estimated_budget`
  - `photo_score`
  - `summary`
  - `days[]`

#### `POST /api/v1/planning/media/placeholders`

用途：
- 返回图片资源占位信息
- 适用于：
  - 旅游地点照片
  - 机位照片
  - 穿搭图片

请求体：

```json
{
  "categories": ["destination", "photo_spot", "outfit"],
  "destination_name": "上海",
  "keywords": ["citywalk", "summer", "photography"]
}
```

响应核心字段：
- `destination_name`
- `assets[]`
  - `category`
  - `items[]`
    - `url`
    - `thumbnail_url`
    - `alt`
    - `provider`
    - `placeholder`

## 5. 常见状态码

- `200 OK`：查询或更新成功
- `201 Created`：创建成功
- `204 No Content`：删除成功
- `400 Bad Request`：请求参数错误，常见于重排列表不完整或重复
- `404 Not Found`：资源不存在
- `409 Conflict`：唯一约束或状态冲突
- `422 Unprocessable Entity`：Pydantic 参数校验失败

## 6. 推荐联调顺序

建议前端按下面顺序接后端：

1. `GET /`
2. `GET /api/v1/health/live`
3. `PUT /api/v1/users/{user_id}/profile`
4. `POST /api/v1/users/{user_id}/trips`
5. `POST /api/v1/trips/{trip_id}/days`
6. `POST /api/v1/trip-days/{trip_day_id}/points`
7. `POST /api/v1/trips/{trip_id}/packing-items`
8. `GET /api/v1/community-posts`
9. `POST /api/v1/planning/destinations`
10. `POST /api/v1/planning/routes`

## 7. curl 示例

### 创建用户档案

```bash
curl -X PUT 'http://127.0.0.1:8000/api/v1/users/11111111-1111-1111-1111-111111111111/profile' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "username": "alice",
    "display_name": "Alice",
    "departure_city": "上海",
    "preferred_styles": ["citywalk", "photography"],
    "budget_level": "medium",
    "language": "zh-CN",
    "timezone": "Asia/Shanghai"
  }'
```

### 创建行程

```bash
curl -X POST 'http://127.0.0.1:8000/api/v1/users/11111111-1111-1111-1111-111111111111/trips' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "上海周末出片游",
    "destination_name": "上海",
    "status": "draft"
  }'
```

### 请求目的地推荐占位接口

```bash
curl -X POST 'http://127.0.0.1:8000/api/v1/planning/destinations' \
  -H 'Content-Type: application/json' \
  -d '{
    "departure_city": "上海",
    "budget_min": 1000,
    "budget_max": 3000,
    "duration_days": 3,
    "travel_style": ["citywalk", "photography"],
    "interests": ["拍照", "建筑"]
  }'
```

## 8. 后续建议

- 把 `core business` 也统一切到 `success/data/meta` 响应格式
- 补充鉴权机制，例如 JWT 或 Session
- 为列表接口补充统一分页返回结构
- 把占位接口替换为真实 AI / Agent Provider
- 补一份 `Apifox / Postman` 导入版接口集合
