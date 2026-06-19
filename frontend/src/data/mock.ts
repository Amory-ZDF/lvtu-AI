/**
 * Mock 数据 - 从 index.html 迁移
 * 后续 Task 20 接入真实接口后可移除
 */

import type { Trip, CommunityPost } from '@/types'

/** 我的行程卡片（首页） */
export interface TripCardData {
  id: string
  title: string
  subtitle: string
  status: 'draft' | 'confirmed'
  gradient: string
  /** 封面图 URL（存在时优先用 LazyImage 渲染，gradient 作为兜底） */
  imageUrl?: string | null
}

export const mockTripCards: TripCardData[] = [
  {
    id: 'dali',
    title: '🌊 大理 · 洱海环线',
    subtitle: '2天1夜 · 3月15-16日',
    status: 'draft',
    gradient: 'linear-gradient(135deg,oklch(0.63 0.17 198),oklch(0.56 0.15 222))',
  },
  {
    id: 'xiamen',
    title: '🏖️ 厦门 · 鼓浪屿',
    subtitle: '3天2夜 · 方案 B · 4月5-7日',
    status: 'confirmed',
    gradient: 'linear-gradient(135deg,oklch(0.62 0.13 42),oklch(0.55 0.15 62))',
  },
]

/** 目的地预览卡片 */
export interface DestinationPreview {
  id: string
  name: string
  region: string
  duration: string
  season: string
  matchScore: string
  price: string
  gradient: string
  tags: string[]
  reason: string
  stops: { day: string; text: string }[]
  highlights: string[]
  recommended?: boolean
}

export const mockDestinations: DestinationPreview[] = [
  {
    id: 'dali',
    name: '🌊 大理 · 洱海环线',
    region: '云南 · 2天1夜 · 四季宜人',
    duration: '2天1夜',
    season: '四季宜人',
    matchScore: '最佳匹配 · 94%',
    price: '¥3,200',
    gradient: 'linear-gradient(135deg,oklch(0.63 0.17 198),oklch(0.56 0.15 222))',
    tags: ['🌿 自然', '📸 高出片', '☕ 文艺', '🐟 美食', '🚴 骑行'],
    reason:
      '💡 洱海沿线有多个绝佳拍照点，骑行节奏轻松，完美匹配你"放松海边 + 拍照出片"的核心诉求。3月气温 15-22°C，适合轻户外穿搭。',
    stops: [
      { day: 'D1', text: '古城 → 喜洲古镇 → 双廊 → 鹿卧山日落' },
      { day: 'D2', text: '龙龛码头日出 → 潘溪村S弯 → 寂照庵 → 返程' },
    ],
    highlights: ['喜洲转角楼', '鹿卧山日落', '龙龛码头日出', 'S弯公路'],
    recommended: true,
  },
  {
    id: 'xiamen',
    name: '🏖️ 厦门 · 鼓浪屿文艺行',
    region: '福建 · 2-3天 · 四季皆可',
    duration: '2-3天',
    season: '四季皆可',
    matchScore: '87% 匹配',
    price: '¥2,800',
    gradient: 'linear-gradient(135deg,oklch(0.62 0.13 42),oklch(0.55 0.15 62))',
    tags: ['📸 高出片', '🍜 美食', '🏛️ 文艺', '🌊 海景'],
    reason:
      '💡 鼓浪屿建筑风格独特，随手拍都很出片，且美食密度高。唯一不足是旺季人流较大，建议工作日出行。',
    stops: [
      { day: 'D1', text: '鼓浪屿 → 日光岩 → 菽庄花园 → 龙头路美食' },
      { day: 'D2', text: '南普陀寺 → 厦大 → 沙坡尾 → 环岛路骑行' },
    ],
    highlights: ['日光岩全景', '菽庄花园', '沙坡尾街区', '环岛路海岸'],
  },
  {
    id: 'qingdao',
    name: '🏝️ 青岛 · 海滨慢时光',
    region: '山东 · 2-3天 · 夏秋最佳',
    duration: '2-3天',
    season: '夏秋最佳',
    matchScore: '82% 匹配',
    price: '¥2,500',
    gradient: 'linear-gradient(135deg,oklch(0.58 0.15 170),oklch(0.50 0.14 195))',
    tags: ['🌊 海景', '🍺 啤酒文化', '🏛️ 德式建筑', '🦐 海鲜'],
    reason:
      '💡 青岛海滨线非常适合轻松周末游，德式建筑群很适合拍照。当前季节稍冷，建议备一件薄外套。',
    stops: [
      { day: 'D1', text: '栈桥 → 天主教堂 → 八大关 → 啤酒博物馆' },
      { day: 'D2', text: '崂山 → 仰口沙滩 → 台东夜市' },
    ],
    highlights: ['八大关银杏', '天主教堂', '栈桥海鸥', '崂山日出'],
  },
]

/** 方案对比卡片 */
export interface PlanOption {
  id: 'A' | 'B'
  title: string
  subtitle: string
  price: string
  metrics: { level: 'high' | 'mid' | 'low'; label: string }[]
  description: string
}

export const mockPlanOptions: PlanOption[] = [
  {
    id: 'A',
    title: '🌿 轻松出片线',
    subtitle: '慢节奏深度体验',
    price: '¥3,200',
    metrics: [
      { level: 'high', label: '出片指数 · 高' },
      { level: 'high', label: '轻松程度 · 高' },
      { level: 'mid', label: '节奏密度 · 中低' },
      { level: 'high', label: '美食覆盖 · 高' },
    ],
    description: '每天 3-4 个景点，留足拍照时间。适合想要深度体验的你。',
  },
  {
    id: 'B',
    title: '🏃 高效打卡线',
    subtitle: '覆盖更多景点',
    price: '¥2,800',
    metrics: [
      { level: 'high', label: '出片指数 · 高' },
      { level: 'mid', label: '轻松程度 · 中' },
      { level: 'high', label: '节奏密度 · 高' },
      { level: 'mid', label: '美食覆盖 · 中' },
    ],
    description: '每天 5-6 个景点，经典机位一网打尽。适合想要玩遍精华的你。',
  },
]

/** 行程点（用于拖拽排序） */
export interface StopCardData {
  id: string
  time: string
  title: string
  desc: string
  spotId?: string
  outfitId?: string
}

export const mockDay1Stops: StopCardData[] = [
  { id: 'depart', time: '09:00', title: '古城出发 · 租电动车', desc: '古城南门 · ¥80/天' },
  {
    id: 'xizhou',
    time: '10:00',
    title: '喜洲古镇',
    desc: '白族民居 · 转角楼 · 喜洲粑粑',
    spotId: 'xizhou-corner',
    outfitId: 'd1-morning',
  },
  { id: 'lunch', time: '12:30', title: '翰林餐厅 · 午餐', desc: '地道白族菜 · ¥60/人' },
  {
    id: 'shuanglang',
    time: '14:00',
    title: '双廊古镇 · 玉几岛',
    desc: '洱海最美观景段 · 下午顺光',
    spotId: 'xizhou-corner',
    outfitId: 'd1-afternoon',
  },
  {
    id: 'luwoshan',
    time: '18:00',
    title: '鹿卧山 · 日落',
    desc: '日落约 18:45',
    spotId: 'luwoshan',
  },
]

export const mockDay2Stops: StopCardData[] = [
  {
    id: 'longkan',
    time: '07:20',
    title: '龙龛码头 · 日出',
    desc: '距离古城最近 · 日出约 7:20',
    spotId: 'longkan',
  },
  {
    id: 'swan',
    time: '10:00',
    title: '潘溪村 S 弯',
    desc: '上午人少光线好',
    spotId: 'swan',
    outfitId: 'd2-morning',
  },
  { id: 'jizhaoan', time: '13:00', title: '寂照庵 · 素斋', desc: '最美尼姑庵 · 多肉花园' },
  { id: 'return', time: '16:00', title: '返程 · 大理站', desc: '预留 1 小时前往车站' },
]

/** 预算条 */
export const mockBudget = [
  { icon: '🏨', label: '住宿', amount: '¥400' },
  { icon: '🚗', label: '交通', amount: '¥300' },
  { icon: '🍜', label: '餐饮', amount: '¥400' },
  { icon: '🎫', label: '门票', amount: '¥200' },
  { icon: '🎒', label: '其他', amount: '¥200' },
]

/** 穿搭卡片 */
export interface OutfitCardData {
  id: string
  sceneTag: string
  emoji: string
  title: string
  desc: string
  gradient: string
}

export interface OutfitDayData {
  dayBadge: 'd1' | 'd2'
  dayLabel: string
  title: string
  cards: OutfitCardData[]
}

export const mockOutfitDays: OutfitDayData[] = [
  {
    dayBadge: 'd1',
    dayLabel: 'Day 1',
    title: '洱海骑行 + 双廊下午茶',
    cards: [
      {
        id: 'd1-morning',
        sceneTag: '上午 · 喜洲',
        emoji: '🧥👗',
        title: '法式碎花裙 + 针织开衫',
        desc: '米白开衫配碎花长裙，喜洲白族民居前法式田园氛围。',
        gradient: 'linear-gradient(135deg,oklch(0.88 0.06 180),oklch(0.82 0.05 215))',
      },
      {
        id: 'd1-afternoon',
        sceneTag: '下午 · 双廊',
        emoji: '👒🕶️',
        title: '白色亚麻套装 + 草帽',
        desc: '洱海边白色系最上镜。亚麻透气，草帽防晒同时增加度假感。',
        gradient: 'linear-gradient(135deg,oklch(0.85 0.05 45),oklch(0.78 0.06 70))',
      },
      {
        id: 'd1-evening',
        sceneTag: '傍晚 · 日落',
        emoji: '🧥🧣',
        title: '轻薄风衣 + 围巾',
        desc: '日落降温，在亚麻套装外加卡其色风衣，保暖同时适合剪影拍摄。',
        gradient: 'linear-gradient(135deg,oklch(0.78 0.06 30),oklch(0.70 0.08 55))',
      },
    ],
  },
  {
    dayBadge: 'd2',
    dayLabel: 'Day 2',
    title: '日出拍摄 + S弯街拍 + 山寺漫步',
    cards: [
      {
        id: 'd2-sunrise',
        sceneTag: '清晨 · 日出',
        emoji: '🧥🧣',
        title: '薄羽绒 + 围巾 + 长裤',
        desc: '码头清晨约 8-10°C，注意保暖。深色系在金色晨光中形成高级对比。',
        gradient: 'linear-gradient(135deg,oklch(0.72 0.06 25),oklch(0.64 0.08 50))',
      },
      {
        id: 'd2-morning',
        sceneTag: '上午 · S弯',
        emoji: '🧶👖',
        title: '条纹针织 + 宽松牛仔裤',
        desc: 'S 弯偏向日系街拍风格，条纹衫配浅色牛仔裤，清新自然。',
        gradient: 'linear-gradient(135deg,oklch(0.80 0.07 260),oklch(0.74 0.06 290))',
      },
      {
        id: 'd2-afternoon',
        sceneTag: '下午 · 寂照庵',
        emoji: '🧥👟',
        title: '宽松衬衫 + 阔腿裤',
        desc: '棉麻材质贴合山寺清幽氛围，平底鞋方便爬坡，多肉花园里很出片。',
        gradient: 'linear-gradient(135deg,oklch(0.84 0.05 150),oklch(0.78 0.06 175))',
      },
    ],
  },
]

/** 必带单品 */
export const mockEssentials = [
  '🧴 防晒霜 SPF50+',
  '🕶️ 墨镜',
  '👒 宽檐草帽',
  '🧥 薄外套 / 开衫',
  '👟 舒适小白鞋',
  '📷 相机 / 手机支架',
  '👜 帆布包',
  '💧 便携水杯',
]

/** 机位卡片 */
export interface SpotCardData {
  id: string
  timePill: string
  title: string
  subtitle: string
  gradient: string
  compositionTitle: string
  composition: string
  outfitTitle?: string
  outfit?: string
  warningTitle?: string
  warning?: string
  tags: { cls: 'best' | 'angle' | 'gear' | 'style'; text: string }[]
}

export const mockSpots: SpotCardData[] = [
  {
    id: 'xizhou-corner',
    timePill: '🌅 17:00—18:30',
    title: '喜洲 · 转角楼',
    subtitle: '白族建筑美学 · 下午顺光',
    gradient: 'linear-gradient(135deg,oklch(0.56 0.18 28),oklch(0.48 0.16 48))',
    compositionTitle: '📐 构图建议',
    composition:
      '站在转角楼对面马路边，低角度仰拍，将蓝天和飞檐一起收入画面。人物在转角处自然走动抓拍最佳。',
    outfitTitle: '👗 穿搭匹配',
    outfit:
      '法式碎花裙 + 米白开衫，与青瓦白墙形成冷暖对比。避免全白（与白墙融为一体）。',
    tags: [
      { cls: 'best', text: '⭐ 高出片' },
      { cls: 'angle', text: '建筑·仰拍' },
      { cls: 'gear', text: '手机即可' },
    ],
  },
  {
    id: 'luwoshan',
    timePill: '🌇 18:00—19:00',
    title: '鹿卧山 · 日落',
    subtitle: '洱海最美日落 · 剪影大片',
    gradient: 'linear-gradient(135deg,oklch(0.58 0.17 205),oklch(0.48 0.16 225))',
    compositionTitle: '📐 构图建议',
    composition:
      '日落前 20 分钟抵达，以枯树为前景，人物站水边。逆光拍剪影，侧光拍半身人像。长焦压缩景深更好。',
    warningTitle: '⚠️ 注意',
    warning: '日落后骤降约 8°C，带外套。周末人多，建议提前 30 分钟占位。',
    tags: [
      { cls: 'best', text: '⭐ 高出片' },
      { cls: 'angle', text: '逆光·剪影' },
      { cls: 'gear', text: '建议长焦' },
    ],
  },
  {
    id: 'longkan',
    timePill: '🌄 07:10—07:40',
    title: '龙龛码头 · 日出',
    subtitle: '金色晨光 · 水面倒影',
    gradient: 'linear-gradient(135deg,oklch(0.63 0.14 58),oklch(0.54 0.15 78))',
    compositionTitle: '📐 构图建议',
    composition:
      '以木栈道为引导线，人物站栈道尽头或侧坐边缘。日出金光 + 水面倒影构成完美对称构图，手机即可出片。',
    outfitTitle: '👗 穿搭匹配',
    outfit:
      '深色系（藏蓝/深灰）在金色晨光中形成高级对比。围巾可作道具增加画面层次。',
    tags: [
      { cls: 'best', text: '⭐ 高出片' },
      { cls: 'angle', text: '对称·倒影' },
      { cls: 'gear', text: '手机即可' },
    ],
  },
  {
    id: 'swan',
    timePill: '☀️ 10:00—12:00',
    title: '潘溪村 · S 弯',
    subtitle: '网红公路 · 骑行抓拍',
    gradient: 'linear-gradient(135deg,oklch(0.56 0.16 215),oklch(0.48 0.14 235))',
    compositionTitle: '📐 构图建议',
    composition:
      '站在 S 弯外侧，用公路曲线做引导线。上午阳光侧后方打来，面部光线柔和。可尝试骑行中动态抓拍。',
    warningTitle: '⚠️ 避坑',
    warning: '下午排队严重（有时等 30 分钟+），强烈建议上午 10 点前到达，避开周末高峰。',
    tags: [
      { cls: 'best', text: '⭐ 高出片' },
      { cls: 'angle', text: '公路·引导线' },
      { cls: 'gear', text: '手机即可' },
    ],
  },
]

/** 机位详情数据 */
export interface SpotDetailData {
  name: string
  hero: string
  time: string
  rate: string
  difficulty: string
  difficultyLabel: string
  location: string
  composition: string
  outfit: string
  outfitId: string | null
  tags: { c: 'best' | 'angle' | 'gear' | 'style'; t: string }[]
  warning?: string
}

export const mockSpotDetails: Record<string, SpotDetailData> = {
  'xizhou-corner': {
    name: '喜洲 · 转角楼',
    hero: 'linear-gradient(135deg,oklch(0.56 0.18 28),oklch(0.48 0.16 48))',
    time: '🌅 最佳时段 17:00—18:30',
    rate: '94%',
    difficulty: '★★☆☆☆',
    difficultyLabel: '简单',
    location: '云南省大理市喜洲古镇 · 转角楼',
    composition:
      '站在转角楼对面马路边，低角度仰拍，将蓝天和飞檐一起收入画面。人物在转角处自然走动，抓拍效果最佳。下午顺光，光线柔和。',
    outfit:
      '法式碎花裙 + 米白开衫，与白族青瓦白墙形成冷暖对比。避免穿全白（与白墙融为一体）。',
    outfitId: 'd1-morning',
    tags: [
      { c: 'best', t: '⭐ 高出片' },
      { c: 'angle', t: '建筑·仰拍' },
      { c: 'gear', t: '手机即可' },
    ],
  },
  luwoshan: {
    name: '鹿卧山 · 日落',
    hero: 'linear-gradient(135deg,oklch(0.58 0.17 205),oklch(0.48 0.16 225))',
    time: '🌇 最佳时段 18:00—19:00',
    rate: '96%',
    difficulty: '★★★☆☆',
    difficultyLabel: '中等',
    location: '云南省大理市环海东路 · 鹿卧山遗址',
    composition:
      '日落前 20 分钟抵达，以枯树为前景，人物站在水边。逆光拍摄剪影，侧光拍半身人像。建议使用长焦镜头压缩景深，能拍到洱海和远山层叠效果。',
    outfit:
      '轻薄风衣 + 围巾，日落后温度骤降约 8°C，务必带外套。深色系在暖色日落中形成高级对比。',
    outfitId: 'd1-evening',
    tags: [
      { c: 'best', t: '⭐ 高出片' },
      { c: 'angle', t: '逆光·剪影' },
      { c: 'gear', t: '建议长焦' },
    ],
    warning: '日落后温度骤降约 8°C，带外套。周末人多，建议提前 30 分钟占位。',
  },
  longkan: {
    name: '龙龛码头 · 日出',
    hero: 'linear-gradient(135deg,oklch(0.63 0.14 58),oklch(0.54 0.15 78))',
    time: '🌄 最佳时段 07:10—07:40',
    rate: '92%',
    difficulty: '★★☆☆☆',
    difficultyLabel: '简单',
    location: '云南省大理市龙龛码头 · 距离古城 3km',
    composition:
      '以木栈道为引导线，人物站在栈道尽头或侧坐栈道边缘。日出金色光线与水面倒影构成完美对称构图。手机即可出片，无需专业设备。',
    outfit:
      '薄羽绒 + 围巾 + 长裤，码头清晨约 8-10°C，注意保暖。深色系（藏蓝/深灰）在金色晨光中形成高级对比。围巾也是很好的拍摄道具。',
    outfitId: 'd2-sunrise',
    tags: [
      { c: 'best', t: '⭐ 高出片' },
      { c: 'angle', t: '对称·倒影' },
      { c: 'gear', t: '手机即可' },
    ],
  },
  swan: {
    name: '潘溪村 · S 弯',
    hero: 'linear-gradient(135deg,oklch(0.56 0.16 215),oklch(0.48 0.14 235))',
    time: '☀️ 最佳时段 10:00—12:00',
    rate: '90%',
    difficulty: '★★☆☆☆',
    difficultyLabel: '简单',
    location: '云南省大理市潘溪村 · 洱海生态廊道 S 弯段',
    composition:
      '站在 S 弯外侧，用公路曲线做引导线。上午阳光从侧后方打过来，面部光线柔和。可尝试骑行中的动态抓拍，或公路中央的远景人像。',
    outfit: '条纹针织衫 + 宽松牛仔裤，偏向日系街拍风格。上午 10 点前到达人少，光线最好。',
    outfitId: 'd2-morning',
    tags: [
      { c: 'best', t: '⭐ 高出片' },
      { c: 'angle', t: '公路·引导线' },
      { c: 'gear', t: '手机即可' },
    ],
    warning: '下午排队严重（有时等 30 分钟+），强烈建议上午 10 点前到达。',
  },
}

/** 穿搭详情数据 */
export interface OutfitDetailData {
  name: string
  hero: string
  scene: string
  weather: string
  items: string[]
  reason: string
  spotId: string | null
}

export const mockOutfitDetails: Record<string, OutfitDetailData> = {
  'd1-morning': {
    name: '法式碎花裙 + 针织开衫',
    hero: 'linear-gradient(135deg,oklch(0.88 0.06 180),oklch(0.82 0.05 215))',
    scene: '喜洲古镇 · 上午',
    weather: '☀️ 晴朗 20°C',
    items: ['米白针织开衫', '碎花连衣裙', '帆布小白鞋', '宽檐草帽（可选）'],
    reason:
      '米白开衫搭配碎花长裙，在白族青瓦白墙前营造法式田园氛围。骑行时可扎起裙摆，白色系在砖红色建筑前形成温柔对比。',
    spotId: 'xizhou-corner',
  },
  'd1-afternoon': {
    name: '白色亚麻套装 + 草帽',
    hero: 'linear-gradient(135deg,oklch(0.85 0.05 45),oklch(0.78 0.06 70))',
    scene: '双廊古镇 · 下午',
    weather: '☀️ 晴朗 22°C',
    items: ['白色亚麻上衣', '亚麻阔腿裤', '宽檐草帽', '墨镜', '帆布包'],
    reason:
      '洱海边白色系最上镜。亚麻材质透气舒适，下午阳光充足时是最佳拍摄时间。草帽防晒同时增添度假感，搭配墨镜轻松出片。',
    spotId: 'xizhou-corner',
  },
  'd1-evening': {
    name: '轻薄风衣 + 围巾',
    hero: 'linear-gradient(135deg,oklch(0.78 0.06 30),oklch(0.70 0.08 55))',
    scene: '鹿卧山 · 傍晚',
    weather: '🌅 日落 18:45 · 温度下降',
    items: ['卡其色轻薄风衣', '围巾', '白色亚麻套装（内搭）'],
    reason:
      '日落时分温度开始下降（约 15°C），在亚麻套装外加一件卡其色风衣，保暖同时适合剪影拍摄。围巾飘动可增加画面动感。',
    spotId: 'luwoshan',
  },
  'd2-sunrise': {
    name: '薄羽绒 + 围巾 + 长裤',
    hero: 'linear-gradient(135deg,oklch(0.72 0.06 25),oklch(0.64 0.08 50))',
    scene: '龙龛码头 · 清晨',
    weather: '🌄 日出 7:20 · 8-10°C',
    items: ['轻薄羽绒服', '保暖围巾', '深色长裤', '手套（可选）'],
    reason:
      '码头清晨约 8-10°C 且有湖风，务必保暖。深色系在金色晨光中形成高级对比。围巾既保暖又可作拍摄道具增加层次感。',
    spotId: 'longkan',
  },
  'd2-morning': {
    name: '条纹针织衫 + 宽松牛仔裤',
    hero: 'linear-gradient(135deg,oklch(0.80 0.07 260),oklch(0.74 0.06 290))',
    scene: '潘溪村 S 弯 · 上午',
    weather: '⛅ 多云 18°C',
    items: ['细条纹针织衫', '浅色宽松牛仔裤', '帆布小白鞋'],
    reason:
      'S 弯偏向日系街拍风格，条纹衫搭配浅色牛仔裤清新自然。上午 10 点人少光线好，是拍摄的最佳窗口。',
    spotId: 'swan',
  },
  'd2-afternoon': {
    name: '宽松衬衫 + 阔腿裤',
    hero: 'linear-gradient(135deg,oklch(0.84 0.05 150),oklch(0.78 0.06 175))',
    scene: '寂照庵 · 下午',
    weather: '⛅ 多云 20°C',
    items: ['棉麻宽松衬衫', '阔腿裤', '平底鞋'],
    reason:
      '山寺环境清幽，棉麻材质贴合氛围。平底鞋方便爬坡，浅色系在多肉花园里很出片。整体偏禅意自然风。',
    spotId: null,
  },
}

/** 打包清单 */
export interface PackItemData {
  id: string
  name: string
  packed: boolean
}

export interface PackCategoryData {
  id: string
  title: string
  placeholder: string
  items: PackItemData[]
}

export const mockPackCategories: PackCategoryData[] = [
  {
    id: 'packClothes',
    title: '👗 衣物',
    placeholder: '添加衣物...',
    items: [
      { id: 'c1', name: '碎花连衣裙 ×1', packed: true },
      { id: 'c2', name: '米白针织开衫 ×1', packed: true },
      { id: 'c3', name: '白色亚麻套装 ×1', packed: false },
      { id: 'c4', name: '条纹针织衫 ×1', packed: true },
      { id: 'c5', name: '宽松牛仔裤 ×1', packed: false },
      { id: 'c6', name: '轻薄风衣 ×1', packed: false },
      { id: 'c7', name: '舒适小白鞋 ×1', packed: true },
    ],
  },
  {
    id: 'packSkincare',
    title: '🧴 护肤 & 防护',
    placeholder: '添加防护用品...',
    items: [
      { id: 's1', name: '防晒霜 SPF50+', packed: true },
      { id: 's2', name: '保湿面膜 ×2', packed: false },
      { id: 's3', name: '润唇膏', packed: false },
      { id: 's4', name: '墨镜', packed: false },
    ],
  },
  {
    id: 'packGear',
    title: '📷 数码 & 其他',
    placeholder: '添加物品...',
    items: [
      { id: 'g1', name: '手机三脚架', packed: false },
      { id: 'g2', name: '充电宝 20000mAh', packed: false },
      { id: 'g3', name: '相机 + 备用电池', packed: false },
      { id: 'g4', name: '宽檐草帽', packed: false },
      { id: 'g5', name: '围巾', packed: false },
      { id: 'g6', name: '便携水杯', packed: false },
    ],
  },
]

/** 社区帖子 */
export interface CommunityPostCard {
  id: string
  title: string
  desc: string
  author: string
  gradient: string
  clickable?: boolean
  /** 封面图 URL（存在时优先用 LazyImage 渲染，gradient 作为兜底） */
  imageUrl?: string | null
}

export const mockCommunityPosts: CommunityPostCard[] = [
  {
    id: 'p1',
    title: '苏苏的大理周末穿搭全记录',
    desc: '洱海环线 · 2天 · 9个机位分享',
    author: '苏苏',
    gradient: 'linear-gradient(135deg,oklch(0.65 0.12 22),oklch(0.57 0.15 45))',
    clickable: true,
  },
  {
    id: 'p2',
    title: '小林的川西秘境日记',
    desc: '四姑娘山 · 3天穿越 · 装备攻略',
    author: '小林',
    gradient: 'linear-gradient(135deg,oklch(0.52 0.13 260),oklch(0.46 0.14 285))',
    clickable: true,
  },
  {
    id: 'p3',
    title: '阿毛的厦门逛吃地图',
    desc: '鼓浪屿 + 中山路 · 日均¥150吃饱',
    author: '阿毛',
    gradient: 'linear-gradient(135deg,oklch(0.58 0.15 170),oklch(0.50 0.13 198))',
  },
  {
    id: 'p4',
    title: 'David 的虎跳峡徒步',
    desc: '2日穿越 · 海拔 2400m · 详细路书',
    author: 'David',
    gradient: 'linear-gradient(135deg,oklch(0.56 0.14 100),oklch(0.50 0.13 120))',
  },
  {
    id: 'p5',
    title: '周末特种兵 · 重庆篇',
    desc: '48h暴走 · 8个出片机位',
    author: 'Rachel',
    gradient: 'linear-gradient(135deg,oklch(0.60 0.15 340),oklch(0.52 0.16 5))',
  },
  {
    id: 'p6',
    title: '青岛老城文艺漫步',
    desc: '德式建筑 + 海边咖啡馆合集',
    author: '小晴',
    gradient: 'linear-gradient(135deg,oklch(0.54 0.14 190),oklch(0.47 0.15 215))',
  },
]

/** 社区标签 */
export const mockCommunityTags = [
  '全部',
  '📸 拍照',
  '🍜 美食',
  '🏔️ 户外',
  '🏖️ 海边',
  '🏛️ 人文',
  '🧘 疗愈',
]

/** 穿搭风格标签 */
export const mockStyleChips = ['📸 出片优先', '👟 舒适轻便', '✨ 法式简约', '🧥 保暖实用']

/** 机位模式标签 */
export const mockSpotModes = ['📷 全部', '✅ 轻松打卡', '⭐ 高出片', '🍃 少排队']

/** 生成步骤文案 */
export const mockGenSteps = [
  '🔍 分析偏好中...',
  '🌤️ 匹配季节与天气...',
  '📍 检索目的地热点数据...',
  '✨ 生成推荐结果...',
]

/** 占位 Trip 列表（用于类型示例） */
export const mockTrips: Trip[] = [
  {
    id: 'dali',
    user_id: 'mock-user',
    title: '🌊 大理 · 洱海环线',
    destination_name: '大理',
    start_date: '2026-03-15',
    end_date: '2026-03-16',
    status: 'draft',
    cover_image_url: null,
    notes: '轻松出片线',
    created_at: '2026-03-01T00:00:00Z',
    updated_at: '2026-03-01T00:00:00Z',
  },
]

/** 占位 CommunityPost 列表 */
export const mockCommunityPostList: CommunityPost[] = mockCommunityPosts.map((p, i) => ({
  id: p.id,
  author_user_id: 'mock-user',
  title: p.title,
  content: p.desc,
  cover_image_url: null,
  status: 'published',
  like_count: 0,
  comment_count: 0,
  published_at: '2026-03-01T00:00:00Z',
  created_at: `2026-03-0${i + 1}T00:00:00Z`,
  updated_at: `2026-03-0${i + 1}T00:00:00Z`,
}))
