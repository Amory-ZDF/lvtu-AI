# 旅图数据与 AI 推荐体系方案

> 目标：让 AI 不凭空生成，而是以旅图自己的目的地、线路、地点、机位、穿搭和用户反馈数据库为基准，完成「目的地推荐」与「具体行程生成」。

## 1. 当前项目现状

项目里已经有一批可复用的基础表：

- `destinations`：目的地知识库
- `photo_spots`：机位知识库
- `outfits`：穿搭知识库
- `travel_notes`：旅行笔记/内容证据
- `destination_candidates`：目的地推荐结果缓存
- `trips` / `trip_days` / `trip_points`：用户最终行程
- `plan_variants`：多方案行程
- `photo_spot_recommendations` / `outfit_recommendations`：针对某次行程生成的推荐结果
- `user_preferences` / `user_behaviors`：用户偏好与行为

但现在还缺 4 层关键能力：

1. **线路库**：某个目的地可以怎么玩，几天几夜，什么节奏，适合什么人。
2. **组合关系库**：哪些地点适合放在同一天，哪些地点距离近/主题一致/时间冲突。
3. **证据来源库**：每条推荐依据来自哪里，可信度如何，是否过期。
4. **检索增强层**：AI 生成前，先从数据库检索相关地点、路线、机位、穿搭、笔记，再让模型组织答案。

## 2. 核心产品链路

```text
用户输入偏好
  ↓
结构化偏好解析：预算 / 天数 / 季节 / 风格 / 兴趣 / 出发地
  ↓
候选目的地召回：目的地库 + 线路库 + 内容证据库 + 用户行为
  ↓
规则与模型排序：季节、预算、交通、风格、数据可信度
  ↓
AI 生成推荐理由：只能基于召回数据解释，不允许编造
  ↓
用户选择目的地
  ↓
召回地点、线路模板、组合关系、机位、穿搭、天气/季节信息
  ↓
生成 2-3 个行程方案
  ↓
规则校验：时间、距离、开闭园、强度、预算、重复地点
  ↓
保存为 trips / trip_days / trip_points / recommendations
```

## 3. 数据从哪里来

### 3.1 官方/半官方基础数据

用于解决“地点是否存在、经纬度、地址、交通距离、天气”等事实问题。

| 数据 | 用途 | 推荐来源 |
|---|---|---|
| POI 名称、地址、经纬度、分类 | 地点基础库 | 高德 POI 搜索 API |
| 地理编码/逆地理编码 | 地址标准化、去重 | 高德地理编码 API |
| 路线距离/通勤时间 | 判断地点能否组合 | 高德路径规划 API |
| 天气 | 影响穿搭和路线可行性 | 高德天气 API / 其他合规天气 API |
| 景区开放时间、门票 | 行程约束 | 景区官网、文旅局官网、人工维护 |

参考文档：

- 高德开放平台 Web 服务 API：https://lbs.amap.com/api/webservice/summary
- 高德 POI 搜索：https://lbs.amap.com/api/webservice/guide/api/search
- 高德路径规划：https://lbs.amap.com/api/webservice/guide/api/direction
- 高德天气查询：https://lbs.amap.com/api/webservice/guide/api/weatherinfo

### 3.2 你自己的产品数据

这是最应该积累的资产。

| 数据 | 来源 | 用途 |
|---|---|---|
| 用户选择了哪个目的地 | 产品行为日志 | 训练推荐排序 |
| 用户保存/删除了哪个行程 | 产品行为日志 | 判断行程质量 |
| 用户修改了哪些地点 | 产品行为日志 | 发现 AI 生成缺陷 |
| 用户最终确认的行程 | 用户行为 | 形成高质量路线样本 |
| 用户评分/反馈 | 评测体系 | 推荐模型迭代 |

### 3.3 人工策展数据

早期数据量不够时，最有效的方式不是盲目爬虫，而是人工策展 + AI 辅助结构化。

建议先做 10 个核心目的地，每个目的地维护：

- 30-50 个 POI
- 5-10 条经典线路
- 20-50 个机位
- 10-20 条穿搭规则
- 30-100 条笔记摘要/证据片段

### 3.4 社交平台/UGC 内容

小红书、携程、马蜂窝等内容可以用于“灵感调研”，但不要把平台原文、图片、用户隐私内容直接抓取并公开入库。推荐策略：

1. 人工浏览或使用合规授权数据源。
2. 只提取结构化事实和你自己的摘要。
3. 保存来源 URL、采集时间、摘要、标签、可信度。
4. 不保存原图，不复制大段原文。
5. 对过期信息设置有效期，例如门票/营业时间 30-90 天复核。

## 4. 数据怎么清洗

建议建立一条固定流水线：

```text
原始数据 raw
  ↓
字段解析 parse
  ↓
标准化 normalize
  ↓
去重 deduplicate
  ↓
地理编码 geocode
  ↓
标签抽取 tag
  ↓
组合关系计算 graph
  ↓
质量评分 quality_score
  ↓
人工抽检 review
  ↓
发布到正式知识库 publish
```

### 4.1 清洗规则

| 清洗项 | 规则 |
|---|---|
| 地点名称 | 建立 canonical_name，别名放 aliases |
| 经纬度 | 用官方 API 校验；缺失则不进入路线生成 |
| 地址 | 省/市/区/详细地址拆分 |
| 标签 | 固定标签体系，不允许自由散乱生成 |
| 时长 | 每个 POI 必须有 recommended_duration_minutes |
| 开放时间 | 不确定时标记 confidence 低，不能强依赖 |
| 预算 | 统一为 price_min / price_max / price_level |
| 季节 | 统一为 spring/summer/autumn/winter/all |
| 适合人群 | couple/family/solo/friends/parent_child |
| 出片属性 | photo_score + photo_tags + best_time_window |
| 穿搭属性 | season + weather + scene + style + items |

### 4.2 LLM 在清洗阶段的作用

LLM 适合做：

- 从笔记摘要中抽取地点、季节、玩法、避坑点。
- 给 POI 打标签。
- 把自然语言路线转成结构化 JSON。
- 生成推荐理由草稿。

LLM 不适合做：

- 编造经纬度。
- 编造门票/营业时间。
- 直接决定两个地点是否交通可行。
- 不带来源地生成“事实”。

关键原则：**LLM 做结构化和表达，事实由数据库和 API 提供。**

## 5. 数据怎么保存

### 5.1 公开仓库与私有数据分离

当前项目已经采用这个原则：

```text
公开 GitHub：代码、文档、脚本、表结构、.env.example
私有目录：数据库 dump、真实种子数据、上传文件
.env/API Key：只放本地，不进 GitHub
```

私有目录：

```bash
/Users/zhangdifei03/Desktop/旅途重构/lv_private_data/
```

### 5.2 建议新增核心表

#### `pois`：地点库

| 字段 | 说明 |
|---|---|
| id | UUID |
| destination_id | 所属目的地 |
| name / canonical_name / aliases | 名称与别名 |
| category | 景点/餐厅/酒店/交通/街区/商场 |
| address | 地址 |
| latitude / longitude | 经纬度 |
| recommended_duration_minutes | 建议游玩时长 |
| price_level / price_min / price_max | 预算 |
| open_hours | 开放时间 JSON |
| best_season | 最佳季节 |
| best_time_window | 最佳时间段 |
| tags | 主题标签 |
| crowd_level | 拥挤程度 |
| confidence_score | 数据可信度 |
| source_ids | 来源证据 |

#### `route_templates`：线路模板

| 字段 | 说明 |
|---|---|
| destination_id | 所属目的地 |
| title | 线路名 |
| duration_days | 天数 |
| pace | relaxed/balanced/intensive |
| theme_tags | 主题 |
| suitable_people | 适合人群 |
| estimated_budget | 预算 |
| route_points | 每天地点顺序 JSON |
| highlights | 亮点 |
| avoid_notes | 避坑 |
| quality_score | 质量评分 |

#### `poi_edges`：地点组合关系

用于回答“哪些地点可以组合在一起”。

| 字段 | 说明 |
|---|---|
| from_poi_id / to_poi_id | 两个地点 |
| travel_minutes | 通勤时间 |
| distance_meters | 距离 |
| transport_mode | walk/drive/transit |
| compatibility_score | 组合分 |
| reason | 为什么适合/不适合组合 |
| conflict_reason | 冲突原因，例如距离远、时间冲突 |

#### `source_documents`：证据来源

| 字段 | 说明 |
|---|---|
| source_type | official/api/manual/user_feedback/ugc_summary |
| source_url | 来源链接 |
| title | 标题 |
| summary | 自己整理的摘要 |
| extracted_facts | 结构化事实 |
| collected_at | 收集时间 |
| expires_at | 过期时间 |
| confidence_score | 来源可信度 |

#### `knowledge_chunks`：RAG 检索片段

| 字段 | 说明 |
|---|---|
| resource_type | destination/poi/route/photo_spot/outfit/note |
| resource_id | 关联资源 |
| chunk_text | 检索文本 |
| embedding | 向量 |
| tags | 标签 |
| confidence_score | 可信度 |

可以使用 PostgreSQL + pgvector 做向量检索。参考：

- pgvector：https://github.com/pgvector/pgvector
- OpenAI Embeddings：https://platform.openai.com/docs/guides/embeddings

## 6. 怎么给 AI 使用

不要把整个数据库直接塞给模型。正确方式是 **先检索，再生成**。

### 6.1 目的地推荐

输入：

```json
{
  "departure_city": "上海",
  "duration_days": 4,
  "budget_min": 3000,
  "budget_max": 6000,
  "season": "autumn",
  "travel_style": ["轻松", "高出片", "美食"],
  "interests": ["海边", "摄影", "城市漫步"]
}
```

流程：

```text
1. SQL 过滤：天数、预算、季节、目的地基础条件
2. 向量召回：找与用户风格相似的线路/笔记/目的地
3. 图关系打分：该目的地下是否有足够可组合 POI
4. 用户行为加权：类似用户更喜欢哪些目的地
5. 排序得到 Top N
6. 把 Top N 的结构化证据给 LLM
7. LLM 只负责生成推荐理由和对比说明
```

推荐排序公式示例：

```text
score =
  0.25 * style_match
+ 0.20 * season_match
+ 0.15 * budget_match
+ 0.15 * route_feasibility
+ 0.10 * photo_outfit_match
+ 0.10 * popularity_or_feedback
+ 0.05 * data_confidence
```

### 6.2 具体行程生成

输入：用户选择的目的地 + 天数 + 节奏 + 兴趣。

流程：

```text
1. 召回目的地信息
2. 召回 POI 列表
3. 召回 route_templates
4. 召回 poi_edges，计算地点组合关系
5. 召回 photo_spots 和 outfits
6. 用规则引擎先生成候选日程骨架
7. LLM 根据骨架生成自然语言方案
8. 校验器检查时间、距离、重复、开闭园、预算
9. 保存到 trips / trip_days / trip_points / plan_variants
```

AI 输出必须是 JSON，例如：

```json
{
  "options": [
    {
      "id": "relaxed-photo-route",
      "title": "轻松高出片路线",
      "pace": "relaxed",
      "estimated_budget": "¥3500-4500",
      "days": [
        {
          "day": 1,
          "theme": "城市初印象 + 日落机位",
          "spots": [
            {
              "poi_id": "...",
              "time_slot": "10:00-12:00",
              "reason": "与用户偏好匹配，因为..."
            }
          ]
        }
      ]
    }
  ]
}
```

### 6.3 穿搭和机位推荐

穿搭和机位不要单独拍脑袋生成，而是跟行程点绑定。

```text
trip_point
  ↓
匹配 photo_spots：同目的地 / 同 POI / 同时间段 / photo_score 高
  ↓
匹配 outfits：季节 / 天气 / 场景 / 活动强度 / 拍照风格
  ↓
LLM 生成解释：为什么这个机位适合、为什么这套穿搭适合
```

穿搭规则示例：

```text
if season=autumn and weather=windy and scene=city_walk:
  推荐：风衣、针织、舒适鞋
  避免：高跟鞋、过薄外套
```

## 7. 数据质量评分体系

每条数据都要有 `confidence_score`。

| 维度 | 权重 | 说明 |
|---|---:|---|
| 来源可信度 | 30% | 官方/实测 > 用户反馈 > UGC 摘要 |
| 新鲜度 | 20% | 越新越高，过期降低 |
| 完整度 | 20% | 经纬度、时长、标签、预算是否齐全 |
| 一致性 | 15% | 多来源是否一致 |
| 产品反馈 | 15% | 用户是否保存、采纳、好评 |

低于阈值的数据只可作为灵感，不可作为事实依据。

```text
confidence_score >= 0.8：可直接用于推荐
0.6 - 0.8：可推荐，但提示不确定字段
< 0.6：只参与召回，不进入最终生成
```

## 8. MVP 数据规模建议

先不要追求全国全量。建议第一阶段只做 10 个高质量目的地。

| 数据类型 | MVP 数量 |
|---|---:|
| 目的地 | 10 个 |
| 每个目的地 POI | 30-50 个 |
| 每个目的地线路模板 | 5-10 条 |
| 每个目的地地点组合边 | 100-300 条 |
| 每个目的地机位 | 20-50 个 |
| 每个目的地穿搭规则 | 10-20 条 |
| 每个目的地证据片段 | 50-100 条 |

优先目的地建议：

```text
北京 / 上海 / 杭州 / 苏州 / 厦门 / 大理 / 成都 / 重庆 / 京都 / 东京
```

## 9. 实施路线图

### Phase 1：数据底座

- 新增 `pois`、`route_templates`、`poi_edges`、`source_documents`、`knowledge_chunks`。
- 保留现有 `destinations`、`photo_spots`、`outfits`。
- 私有目录继续保存真实 seed 数据。
- 写 `import_private_knowledge.py`，从私有 JSON/CSV 导入数据库。

### Phase 2：数据采集与清洗

- 用官方 API 补齐 POI 经纬度、地址、距离。
- 人工整理 10 个目的地核心线路。
- 用 LLM 辅助把笔记摘要结构化。
- 给每条数据打 `confidence_score`。

### Phase 3：目的地推荐升级

- 先用 SQL + 规则生成候选。
- 再用 embedding/RAG 找相似线路和证据。
- 最后让 LLM 生成推荐理由。
- 推荐结果保存到 `destination_candidates`。

### Phase 4：行程生成升级

- 先用线路模板和地点组合图生成日程骨架。
- LLM 只做方案表达和轻量调整。
- 输出后跑校验器。
- 保存到 `trips`、`trip_days`、`trip_points`、`plan_variants`。

### Phase 5：反馈闭环

- 记录用户点击、收藏、删除、修改、确认。
- 用户确认的行程反哺 route_templates。
- 用户删除/修改频繁的点降低质量分。

## 10. 产品经理判断标准

这个系统做得好不好，不看“AI 文案是否华丽”，而看：

1. 推荐是否能解释：为什么推荐这个目的地？
2. 行程是否可执行：时间、距离、预算是否合理？
3. 数据是否可信：每个事实有没有来源？
4. 用户是否少修改：生成后用户改得越少越好。
5. 是否越用越准：用户行为能不能反馈到推荐排序。

最终目标：

```text
AI 不做旅行幻想家，而做基于旅图数据库的旅行产品经理。
```
