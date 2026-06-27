# 旅图样本数据采集执行手册

## 1. 先明确边界

旅图需要的是“可推荐、可解释、可校验”的旅行知识库，不是单纯堆一批网页文本。

不建议直接做：

- 绕过登录态、风控、验证码、反爬机制采集小红书。
- 保存小红书原文、图片、用户头像、用户主页等内容到公开仓库。
- 把第三方平台内容原样展示给用户。

可以做：

- 用官方/授权 API 收集地点基础信息。
- 人工阅读 UGC 后，只保存自己的结构化摘要和来源 URL。
- 用 LLM 辅助从摘要中抽取地点、机位、季节、避坑、穿搭标签。
- 所有真实数据放在 `lv_private_data/`，不进公开 GitHub。

## 2. 有没有官方 API

### 小红书

小红书没有适合“公开搜索全站笔记并批量拿旅行内容”的开放官方 API。实际能用的开放能力通常偏商业、店铺、广告、创作者或合作生态，不适合作为通用旅行笔记数据库来源。

因此，小红书更适合做：

```text
人工灵感调研 / 合规授权数据 / 少量人工摘要
```

而不是作为自动化主数据源。

### 高德地图

高德 Web 服务 API 适合做地点基础数据源：

- POI 搜索：地点名称、地址、经纬度、分类。
- 地理编码：地址标准化。
- 路径规划：计算两个地点能否组合。
- 天气查询：影响穿搭和路线安排。

注意：高德更适合国内目的地。京都、东京等海外目的地需要单独使用 OSM、Google Places 或人工策展，不要直接混在高德城市检索里，否则容易出现城市识别不准。

官方文档：

- Web 服务 API：https://lbs.amap.com/api/webservice/summary
- POI 搜索：https://lbs.amap.com/api/webservice/guide/api/search
- 路径规划：https://lbs.amap.com/api/webservice/guide/api/direction
- 天气查询：https://lbs.amap.com/api/webservice/guide/api/weatherinfo

## 3. 第一阶段采集目标

先做 10 个目的地，每个目的地至少收集：

| 类型 | 数量目标 |
|---|---:|
| POI 候选 | 200-500 |
| 高质量景点 | 30-50 |
| 打卡点/机位候选 | 20-50 |
| 线路模板 | 5-10 |
| 地点组合关系 | 100-300 |
| 穿搭规则 | 10-20 |

优先城市：

```text
北京 / 上海 / 杭州 / 苏州 / 厦门 / 大理 / 成都 / 重庆 / 京都 / 东京
```

## 4. 关键词策略

高德 POI 采集关键词分 4 类：

### 基础景点

```text
景点, 风景名胜, 博物馆, 美术馆, 公园, 古镇, 寺庙
```

### 打卡/机位候选

```text
观景台, 夜景, 日落, 拍照, 网红打卡
```

### 旅行体验点

```text
咖啡, 市集, 街区, 商场, 书店, 展览
```

### 线路补充点

```text
火车站, 机场, 客运站, 地铁站, 酒店
```

## 5. 已实现脚本

脚本：

```bash
backend/scripts/collect_amap_pois.py
```

默认输出到仓库外：

```bash
/Users/zhangdifei03/Desktop/旅途重构/lv_private_data/raw/amap/
```

运行示例：

```bash
cd backend
python -m scripts.collect_amap_pois --cities 北京,上海,杭州 --limit-per-keyword 60
```

建议先采国内城市：

```bash
cd backend
python -m scripts.collect_amap_pois \
  --cities 北京,上海,杭州,苏州,厦门,大理,成都,重庆 \
  --limit-per-keyword 30
```

指定关键词：

```bash
cd backend
python -m scripts.collect_amap_pois \
  --cities 大理 \
  --keywords 景点,风景名胜,拍照,观景台,日落,网红打卡 \
  --limit-per-keyword 80
```

输出文件：

```text
lv_private_data/raw/amap/poi_candidates_YYYYMMDD_HHMMSS.json
lv_private_data/raw/amap/poi_candidates_latest.json
```

## 6. 数据清洗步骤

采集结果不能直接给 AI 用，需要做二次清洗：

```text
raw POI
  ↓
按 AMap source_id 去重
  ↓
按 name + 经纬度二次去重
  ↓
过滤低价值点：酒店、普通公司、无经纬度点、重复商户
  ↓
归类：景点 / 机位 / 餐饮 / 交通 / 街区 / 购物
  ↓
补字段：建议停留时长、最佳季节、适合人群、预算、标签
  ↓
计算地点组合关系：距离、通勤时间、同日可行性
  ↓
进入私有 seed_data，再导入数据库
```

## 7. 给 AI 的方式

不要把原始 POI 列表直接塞给模型。

正确方式：

```text
用户偏好
  ↓
SQL 过滤候选目的地/地点
  ↓
向量召回路线、地点、机位、穿搭、笔记摘要
  ↓
规则排序
  ↓
只把 Top N 结构化数据给 LLM
  ↓
LLM 输出 JSON 行程
  ↓
后端校验后入库
```

## 8. 小红书数据如何安全利用

如果后续一定要参考小红书，建议只做“人工摘要层”：

```text
搜索关键词：大理 拍照 机位 / 京都 红叶 路线
人工阅读 10-20 篇
提取自己的摘要：地点、时间、避坑、穿搭、机位角度
保存 source_url + summary + extracted_facts
不保存原图/原文/用户信息
```

这部分可以进入：

```text
source_documents
travel_notes
knowledge_chunks
```

但不要进入公开 GitHub。
