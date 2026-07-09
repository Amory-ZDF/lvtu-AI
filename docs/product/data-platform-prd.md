# 旅图数据中台 PRD 与埋点方案

## 1. 产品目标

数据中台只回答四类核心经营问题：

1. 用户在核心链路中走到哪一步、从哪一步开始流失。
2. 每个页面用户停留多久，而不是只看全站均值。
3. 每个页面内具体按钮是否被点击，以及点击率是否健康。
4. 用户最终选择了哪些目的地、路线方案和兴趣偏好。

当前版本不展示全站总点击率、全站平均停留、平均会话时长、设备分布、最近事件流水等泛化指标，避免看板变成“什么都有但无法决策”的杂乱后台。

## 2. 页面与权限

- 前端独立入口：`/data-center`
- 历史入口：`/analytics` 自动跳转到 `/data-center`
- 产品主页、侧边栏、普通用户链路不暴露数据中台入口
- 数据中台需要白名单登录
- 白名单账号只能从后端脚本或数据中台页面添加，不能主动注册
- 当前免密白名单登录适合本地测试；生产环境建议升级为邮箱验证码或一次性邀请链接

## 3. 前后端分离数据契约

接口：`GET /api/v1/analytics/dashboard?days=7`

后端只返回四个业务模块，前端只负责渲染，不在前端二次计算核心口径。

```json
{
  "range_days": 7,
  "calculated_at": "2026-07-08T00:00:00Z",
  "funnel": [],
  "page_stays": [],
  "page_buttons": [],
  "selection_groups": []
}
```

### 3.1 转化漏斗 `funnel`

| 字段 | 含义 |
|---|---|
| key | 步骤唯一标识 |
| label | 页面展示名称 |
| users | 当前步骤去重用户数 |
| previous_step_rate | 相邻上一步转化率 |
| overall_rate | 相对第一步整体转化率 |
| dropoff_rate | 相邻上一步流失率 |

### 3.2 页面停留 `page_stays`

| 字段 | 含义 |
|---|---|
| page_path | 页面路径 |
| page_title | 页面标题 |
| views | 页面 PV |
| visitors | 页面 UV |
| avg_stay_seconds | 页面平均停留秒数 |
| p50_stay_seconds | 页面 P50 停留秒数 |

### 3.3 页面按钮点击率 `page_buttons`

| 字段 | 含义 |
|---|---|
| page_path | 按钮所在页面 |
| page_title | 页面标题 |
| button_label | 按钮文案 |
| button_role | 控件类型 |
| clicks | 点击次数 |
| click_users | 点击用户数 |
| page_views | 当前页面 PV 基数 |
| click_rate | 点击率，`clicks / page_views` |
| user_click_rate | 用户点击率，`click_users / page_uv` |

### 3.4 已选择比例 `selection_groups`

| 字段 | 含义 |
|---|---|
| key | 选择分组标识 |
| label | 选择分组名称 |
| total | 当前分组总选择次数 |
| options | 选项列表 |

`options` 字段：

| 字段 | 含义 |
|---|---|
| label | 选项名称 |
| count | 被选择次数 |
| ratio | 选择占比，`count / total` |

## 4. 指标口径

### 4.1 用户去重口径

优先级：

1. 已登录用户：`user_id`
2. 未登录访客：`visitor_id`
3. 兜底：`session_id`

这样可以同时覆盖登录用户和游客，不因为用户未登录就丢失漏斗数据。

### 4.2 转化漏斗

| 步骤 | 事件规则 |
|---|---|
| 访问首页 | `page_view` 且 `page_path = /` |
| 进入偏好输入页 | `page_view` 且 `page_path = /start` |
| 生成目的地推荐 | `destination_recommendation_success` |
| 选择目的地 | `destination_selected` |
| 生成路线方案 | `route_generation_success` |
| 确认路线方案 | `route_option_confirmed` 或 `trip_created` |
| 进入行程详情 | `page_view` 且 `page_path` 以 `/trips/` 开头 |
| 生成穿搭预览 | `outfit_preview_generated` |

计算方式：

- 相邻转化率 = 当前步骤去重用户数 / 上一步去重用户数
- 整体转化率 = 当前步骤去重用户数 / 第一步去重用户数
- 流失率 = `1 - 相邻转化率`

### 4.3 每个页面的停留时长

| 指标 | 计算方式 |
|---|---|
| 页面 PV | 当前 `page_path` 下 `page_view` 事件数 |
| 页面 UV | 当前 `page_path` 下按用户去重 |
| 页面平均停留 | 当前 `page_path` 下 `page_leave/page_heartbeat.duration_ms` 均值 |
| 页面 P50 停留 | 当前 `page_path` 下停留时长中位数 |

### 4.4 每个页面中按钮的点击率

| 指标 | 计算方式 |
|---|---|
| 点击次数 | 当前页面下同一按钮的 click 类事件数 |
| 点击用户数 | 当前页面下点击该按钮的去重用户数 |
| 点击率 | `点击次数 / 当前页面 PV` |
| 用户点击率 | `点击用户数 / 当前页面 UV` |

### 4.5 已选择的比例

| 分组 | 事件规则 | 选项来源 |
|---|---|---|
| 目的地选择占比 | `destination_selected` | `destination_name` / `selection_label` |
| 路线方案点击占比 | `route_option_selected` | `route_title` / `selection_label` / `option_id` |
| 最终方案确认占比 | `route_option_confirmed` | `route_title` / `selection_label` / `option_id` |
| 兴趣偏好选择占比 | metadata 中的 `interests` | 兴趣标签 |

## 5. 埋点方案

### 5.1 自动埋点

前端全局埋点自动采集：

| 场景 | 事件 |
|---|---|
| 路由进入 | `page_view` |
| 路由离开 | `page_leave`，带 `duration_ms` |
| 页面隐藏 | `page_heartbeat`，带 `duration_ms` |
| 点击 button / link / role=button | `button_click` 或 `link_click` |
| 表单提交 | `form_submit` |

按钮文本优先级：

1. `data-analytics-label`
2. `aria-label`
3. `title`
4. input value / name / type
5. textContent
6. id / tagName

### 5.2 业务转化埋点

| 事件名 | 触发时机 | metadata |
|---|---|---|
| `destination_recommendation_success` | 目的地推荐成功 | `destination_count`, `duration_days`, `interests` |
| `destination_selected` | 用户选择目的地 | `destination_name`, `selection_label` |
| `route_generation_success` | 路线生成成功 | `destination_name`, `duration_days`, `option_count` |
| `route_option_selected` | 用户点击某个路线方案 | `route_title`, `selection_label`, `option_id` |
| `route_option_confirmed` | 用户确认某个路线方案 | `route_title`, `selection_label`, `option_id` |
| `trip_created` | 完整行程创建成功 | `destination_name`, `route_title` |
| `outfit_preview_generated` | AI 穿搭预览生成成功 | `outfit_id`, `generated` |

## 6. 数据安全原则

- 埋点不采集输入框正文、密码、Token、API Key、精确定位、身份证等敏感信息。
- 后端会清理 metadata 中的 `password`、`token`、`authorization`、`api_key`、`secret` 等敏感键。
- `.env`、本地数据库、API Key、私有配置不进入 GitHub。
- 上线前需要先执行数据库迁移，再创建数据中台白名单账号。

## 7. 后续迭代建议

1. 将免密白名单升级为邮箱 OTP 或一次性邀请链接。
2. 增加页面筛选：只看首页、偏好页、目的地页、路线页、详情页。
3. 增加导出能力：按当前时间范围导出 CSV。
4. 增加异常指标：目的地生成失败、路线生成失败、AI 生图失败。
5. 增加分群：新用户/老用户、登录/未登录、移动/桌面。
