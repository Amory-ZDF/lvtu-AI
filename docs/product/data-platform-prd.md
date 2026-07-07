# 旅图数据中台 PRD 与埋点方案

## 1. 产品目标

数据中台用于回答三个问题：

1. 用户是否真的能走完「首页 → 偏好输入 → 目的地推荐 → 路线生成 → 行程详情」核心链路。
2. 用户在哪些页面停留、点击和流失。
3. 哪些功能按钮、AI 生成能力、穿搭预览能力被真实使用。

当前版本优先做「可真实入库、可看趋势、可定位问题」的轻量中台，不引入第三方 SDK，所有数据写入自有后端数据库。

## 2. 权限与隐私原则

- 埋点不采集输入框内容、密码、Token、API Key、精确定位、身份证等敏感信息。
- 不存储客户端 IP；仅存储 user_agent、设备类型、页面路径、按钮文本等产品分析必要信息。
- 数据看板接口需要登录。
- 生产环境建议配置 `ANALYTICS_ADMIN_EMAILS`，仅允许指定邮箱查看数据中台。
- `.env` / API Key / 私有数据不进入 GitHub。

## 3. 数据模型

核心表：`analytics_events`

| 字段 | 含义 |
|---|---|
| user_id | 登录用户 ID，未登录为空 |
| visitor_id | 浏览器级匿名访客 ID，localStorage 保存 |
| session_id | 会话 ID，sessionStorage 保存 |
| event_name | 事件名，例如 `page_view`、`button_click` |
| event_category | 事件类别：page / click / engagement / conversion / form |
| page_path | 当前页面路径 |
| page_title | 页面标题 |
| referrer | 来源页面 |
| element_text | 按钮/链接/表单可读文本 |
| element_role | button / a / form 等控件类型 |
| target_url | 链接跳转地址 |
| duration_ms | 停留时长，毫秒 |
| viewport_width / viewport_height | 视口尺寸 |
| device_type | desktop / tablet / mobile |
| user_agent | 浏览器 UA |
| metadata | 业务补充信息，不允许放敏感值 |
| occurred_at | 客户端事件发生时间 |

## 4. 指标体系与计算口径

### 4.1 总览指标

| 指标 | 计算方式 | 用途 |
|---|---|---|
| UV 访客数 | `user_id` 优先，否则 `visitor_id`，否则 `session_id` 去重 | 判断真实访问规模 |
| Sessions 访问会话 | `session_id` 去重 | 判断访问次数 |
| PV 页面浏览 | `event_name = page_view` 的事件数 | 判断页面流量 |
| 登录用户数 | 有 `user_id` 的事件按用户去重 | 判断登录用户活跃 |
| 事件总量 | 当前时间窗口内全部埋点事件数 | 判断埋点覆盖和活跃度 |
| 平均停留时长 | `page_leave/page_heartbeat.duration_ms` 均值 / 1000 | 判断页面内容吸引力 |
| 平均会话时长 | 每个 session 的停留事件 duration 求和后取均值 | 判断单次访问深度 |
| 点击率 CTR | click 类事件数 / PV | 判断界面是否产生操作 |

### 4.2 页面指标

| 指标 | 计算方式 |
|---|---|
| 页面 PV | 某 `page_path` 下 `page_view` 数 |
| 页面 UV | 某 `page_path` 下用户去重 |
| 页面平均停留 | 某 `page_path` 下 `duration_ms` 均值 / 1000 |

### 4.3 按钮指标

| 指标 | 计算方式 |
|---|---|
| 按钮点击次数 | `event_category = click` 且同 `element_text + page_path` 聚合 |
| 按钮点击人数 | 同一按钮下用户去重 |
| 页面按钮热度 | 按点击次数倒序 |

### 4.4 核心漏斗

| 步骤 | 事件规则 |
|---|---|
| 访问首页 | `page_view` 且 `page_path = /` |
| 进入规划页 | `page_view` 且 `page_path = /start` |
| 生成目的地推荐 | `destination_recommendation_success` |
| 生成路线 | `route_generation_success` |
| 进入行程详情 | `page_view` 且 `page_path` 以 `/trips/` 开头 |
| 生成穿搭预览 | `outfit_preview_generated` |

每一步转化率 = 该步骤去重用户数 / 第一步去重用户数。

## 5. 埋点方案

### 5.1 自动埋点

前端全局 `AnalyticsTracker` 自动采集：

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
| `destination_recommendation_success` | 目的地推荐成功 | destination_count, duration_days |
| `route_generation_success` | 路线生成成功 | destination_name, duration_days, option_count |
| `trip_created` | 用户创建完整行程成功 | destination_name, route_title |
| `outfit_preview_generated` | AI 穿搭预览生成成功 | outfit_id, generated |

## 6. 数据中台页面

路径：`/analytics`

模块：

1. 顶部筛选：近 7 / 14 / 30 / 90 天。
2. KPI 卡片：UV、Sessions、PV、平均停留、CTR、登录用户、会话时长、事件总量。
3. 趋势图：每日 events / PV / UV。
4. 热门页面：页面 PV、UV、平均停留。
5. 按钮点击：按钮文案、页面、点击次数、点击人数。
6. 核心漏斗：从首页访问到穿搭预览生成。
7. 设备分布：desktop / tablet / mobile。
8. 最近事件：最近 30 条行为日志。

## 7. 后续迭代建议

1. 增加用户分群：新用户/老用户、登录/未登录、移动/桌面。
2. 增加路径分析：按 session 还原用户访问路径。
3. 增加异常漏斗：路线生成失败、AI 生图失败、登录失败。
4. 增加留存指标：次日/7 日回访。
5. 增加数据导出：CSV / Excel。
6. 增加管理权限：单独的 admin role，而不是只依赖邮箱白名单。
