export const routeMeta = [
  { key: 'home', path: '/', label: '首页', phase: '灵感进入' },
  { key: 'auth', path: '/auth', label: '登录', phase: '登录拦截' },
  { key: 'start', path: '/start', label: '开始行程', phase: '需求输入' },
  {
    key: 'destinations',
    path: '/destinations',
    label: '目的地推荐',
    phase: '地点确认',
  },
  { key: 'compare', path: '/compare', label: '方案对比', phase: '路线选择' },
  {
    key: 'workspace',
    path: '/workspace',
    label: '行程工作台',
    phase: '深度编辑',
  },
  {
    key: 'tripDetail',
    path: '/trip/demo-trip',
    label: '行程详情',
    phase: '执行与分享',
  },
  { key: 'import', path: '/import', label: '导入行程', phase: '导入旁路' },
  { key: 'discover', path: '/discover', label: '推荐页', phase: '灵感扩展' },
  { key: 'community', path: '/community', label: '社区页', phase: '内容回流' },
  {
    key: 'communityDetail',
    path: '/community/demo-post',
    label: '社区详情',
    phase: '同款规划',
  },
  { key: 'myTrips', path: '/my-trips', label: '我的行程', phase: '资产管理' },
]

export const flowBaseline = [
  {
    name: '主路径：先地后线',
    steps: [
      '首页/推荐/社区进入',
      '开始行程收集偏好',
      '先返回候选目的地',
      '确认后进入方案对比',
      '再进入工作台与详情',
    ],
  },
  {
    name: '导入旁路',
    steps: ['导入行程', '解析确认', '补全预算/时长/交通', '进入工作台编辑'],
  },
  {
    name: '社区旁路',
    steps: [
      '社区卡片进入',
      '查看详情与预算摘要',
      '预填开始行程',
      '进入目的地确认与路线生成',
    ],
  },
]

export const responsibilityBaseline = [
  'pages: 路由装配、页面编排和 CTA 上下文。',
  'components: 复用展示模块，不持有跨页结构。',
  'modals: 登录、导入确认、分享发布、删除确认等独立容器。',
  'data: 维护页面清单、mock、弹窗与状态注册表。',
  'hooks: 本地演示态管理，不依赖真实后端。',
  'styles: 维护设计 token 与全局布局约束。',
]

export const dataModelBaseline = [
  {
    key: 'destinations',
    label: '目的地',
    fields: ['name', 'matchScore', 'budget', 'season', 'vibe'],
  },
  {
    key: 'plans',
    label: '方案',
    fields: ['title', 'days', 'budget', 'pace', 'photoScore'],
  },
  {
    key: 'trips',
    label: '行程',
    fields: ['title', 'status', 'duration', 'destination', 'lastAction'],
  },
  {
    key: 'communityPosts',
    label: '社区内容',
    fields: ['title', 'author', 'likes', 'routeType', 'destination'],
  },
  {
    key: 'outfits',
    label: '穿搭',
    fields: ['scene', 'weather', 'heroItem', 'mood'],
  },
  {
    key: 'cameraSpots',
    label: '机位',
    fields: ['name', 'bestTime', 'queueLevel', 'shotType'],
  },
]

export const statusRegistry = [
  {
    key: 'generation',
    label: 'AI 生成',
    options: ['loading', 'success', 'error'],
  },
  {
    key: 'import',
    label: '导入解析',
    options: ['confirm', 'loading', 'success', 'error'],
  },
  { key: 'save', label: '保存草稿', options: ['confirm', 'success', 'error'] },
  {
    key: 'publish',
    label: '社区发布',
    options: ['empty', 'loading', 'success', 'error'],
  },
  {
    key: 'delete',
    label: '删除行程',
    options: ['confirm', 'success', 'error'],
  },
]

export const modalRegistry = {
  auth: {
    title: '登录 / 注册弹窗',
    body: '用于保存行程、收藏、评论、协同邀请时的统一拦截入口。',
    highlights: [
      '邮箱/验证码双入口',
      '登录成功后回原任务上下文',
      '展示保存与分享权益',
    ],
  },
  tripBrief: {
    title: '开始行程补充信息浮层',
    body: '承接偏好、预算、季节、同行人与风格问答。',
    highlights: [
      '支持不知道去哪',
      '支持已有目的地再校验',
      '生成阶段展示 loading 文案',
    ],
  },
  destinationCompare: {
    title: '目的地对比浮层',
    body: '展示 3 个候选目的地的预算、天气、氛围与出片指数差异。',
    highlights: ['支持加入对比', '支持换一批', '确认目的地前不进路线生成'],
  },
  planConfirm: {
    title: '方案选择确认',
    body: '确认路线版本、预算和节奏后再进入工作台。',
    highlights: ['保留备选方案', '明确预算差异', '确认后写入工作台草稿'],
  },
  importConfirm: {
    title: '导入解析确认',
    body: '检查外部链接/文档解析结果，补充预算、时长、交通。',
    highlights: ['支持人工修正', '补全缺失字段', '确认后补全工作台'],
  },
  outfitDetail: {
    title: '穿搭详情弹窗',
    body: '绑定天气、地点、时间和拍照意图展示穿搭建议。',
    highlights: ['支持切换风格', '支持加入打包清单', '与行程节点关联'],
  },
  cameraSpot: {
    title: '机位详情弹窗',
    body: '提供最佳到访时间、构图说明和排队强度。',
    highlights: ['支持高出片切换', '支持地图跳转', '与景点节点绑定'],
  },
  deleteConfirm: {
    title: '删除行程确认',
    body: '用于我的行程页删除草稿或已完成行程。',
    highlights: ['展示不可逆提醒', '支持二次确认', '删除后更新列表状态'],
  },
  shareCommunity: {
    title: '分享到社区',
    body: '复用当前行程摘要、亮点图文和标签生成分享内容。',
    highlights: ['支持分享模板', '支持预算与机位亮点', '可跳转发布态'],
  },
  publishCommunity: {
    title: '发布社区内容',
    body: '从社区页发起帖子发布，支持引用现有行程。',
    highlights: [
      '支持选择引用行程',
      '支持草稿与发布结果态',
      '发布成功回流社区流',
    ],
  },
}

export const mockData = {
  destinations: [
    {
      id: 'dest-kyoto',
      name: '京都慢闪',
      matchScore: '94%',
      budget: '4200-5800',
      season: '11 月红叶',
      vibe: '寺院、咖啡、胶片感',
    },
    {
      id: 'dest-chiangmai',
      name: '清迈雨后',
      matchScore: '89%',
      budget: '3200-4600',
      season: '10 月凉季前',
      vibe: '慢生活、夜市、手作',
    },
    {
      id: 'dest-yogyakarta',
      name: '日惹火山线',
      matchScore: '84%',
      budget: '3500-5200',
      season: '旱季尾声',
      vibe: '自然、探险、日出机位',
    },
  ],
  plans: [
    {
      id: 'plan-a',
      title: '高出片慢游线',
      days: '4 天 3 晚',
      budget: '5600',
      pace: '松弛',
      photoScore: '9.4',
    },
    {
      id: 'plan-b',
      title: '效率打卡线',
      days: '3 天 2 晚',
      budget: '4300',
      pace: '紧凑',
      photoScore: '8.6',
    },
    {
      id: 'plan-c',
      title: '朋友同行平衡线',
      days: '5 天 4 晚',
      budget: '6100',
      pace: '平衡',
      photoScore: '8.9',
    },
  ],
  trips: [
    {
      id: 'demo-trip',
      title: '京都银杏与夜枫 4 日',
      status: '草稿',
      duration: '4 天',
      destination: '京都',
      lastAction: '20 分钟前更新预算',
    },
    {
      id: 'trip-chiangmai',
      title: '清迈周末回血 3 日',
      status: '已保存',
      duration: '3 天',
      destination: '清迈',
      lastAction: '昨天查看穿搭建议',
    },
    {
      id: 'trip-seoul',
      title: '首尔春日咖啡快闪',
      status: '已完成',
      duration: '5 天',
      destination: '首尔',
      lastAction: '已分享至社区',
    },
  ],
  communityPosts: [
    {
      id: 'demo-post',
      title: '京都 4 日夜枫机位清单',
      author: 'Mina',
      likes: 326,
      routeType: '高出片慢游',
      destination: '京都',
    },
    {
      id: 'post-chiangmai',
      title: '清迈雨季也能穿得轻盈',
      author: 'Suki',
      likes: 218,
      routeType: '轻装回血',
      destination: '清迈',
    },
    {
      id: 'post-dali',
      title: '大理洱海边的低饱和路线',
      author: 'Kiko',
      likes: 412,
      routeType: '灵感种草',
      destination: '大理',
    },
  ],
  outfits: [
    {
      id: 'outfit-1',
      scene: '寺院晨拍',
      weather: '12-18C',
      heroItem: '米白针织披肩',
      mood: '安静胶片',
    },
    {
      id: 'outfit-2',
      scene: '夜市逛吃',
      weather: '18-24C',
      heroItem: '轻量牛仔外套',
      mood: '轻松街头',
    },
    {
      id: 'outfit-3',
      scene: '海边日落',
      weather: '24-28C',
      heroItem: '低饱和吊带长裙',
      mood: '轻透松弛',
    },
  ],
  cameraSpots: [
    {
      id: 'camera-1',
      name: '清水寺三重塔侧坡',
      bestTime: '07:10',
      queueLevel: '低',
      shotType: '长焦压缩层次',
    },
    {
      id: 'camera-2',
      name: '八坂之塔转角',
      bestTime: '17:40',
      queueLevel: '中',
      shotType: '广角街景',
    },
    {
      id: 'camera-3',
      name: '鴨川桥面',
      bestTime: '18:20',
      queueLevel: '低',
      shotType: '逆光剪影',
    },
  ],
}

export const pageBaseline = {
  home: {
    title: '首页',
    summary: '灵感入口页，承接开始行程、推荐与社区精选。',
    modules: [
      'Hero CTA',
      '热门标签',
      '候选目的地卡片',
      '社区精选',
      '登录拦截提示',
    ],
    datasets: ['destinations', 'communityPosts'],
    statusKeys: ['generation', 'save'],
    actions: [
      { label: '开始行程问答', modal: 'tripBrief', status: 'generation' },
      { label: '保存灵感前登录', modal: 'auth', status: 'save' },
    ],
  },
  auth: {
    title: '注册 / 登录页',
    summary: '关键节点触发的统一登录拦截态。',
    modules: ['邮箱登录', '验证码登录', '权益说明', '回原任务上下文'],
    datasets: ['trips'],
    statusKeys: ['save'],
    actions: [{ label: '打开登录弹窗', modal: 'auth', status: 'save' }],
  },
  start: {
    title: '开始行程页',
    summary: '收集偏好与约束，优先用于推荐候选目的地。',
    modules: [
      '目的地输入',
      '预算/季节/时长',
      '风格偏好',
      '阶段式 loading 反馈',
    ],
    datasets: ['destinations'],
    statusKeys: ['generation'],
    actions: [
      { label: '补充偏好信息', modal: 'tripBrief', status: 'generation' },
    ],
  },
  destinations: {
    title: '目的地推荐结果页',
    summary: '展示 3 个候选目的地、匹配原因与加入对比操作。',
    modules: ['候选目的地卡片', '推荐理由', '换一批', '加入对比'],
    datasets: ['destinations'],
    statusKeys: ['generation'],
    actions: [
      {
        label: '打开目的地对比',
        modal: 'destinationCompare',
        status: 'generation',
      },
      {
        label: '确认目的地并选方案',
        modal: 'planConfirm',
        status: 'generation',
      },
    ],
  },
  compare: {
    title: '方案对比页',
    summary: '围绕已确认目的地比对路线、预算、节奏与出片指数。',
    modules: ['方案对比矩阵', '预算差异', '节奏与出片指数', '保留备选'],
    datasets: ['plans'],
    statusKeys: ['generation', 'save'],
    actions: [{ label: '确认路线方案', modal: 'planConfirm', status: 'save' }],
  },
  workspace: {
    title: '行程工作台',
    summary: '承接连续编辑、局部重算、穿搭和机位入口。',
    modules: ['日程列表', 'AI 改写区', '预算天气侧栏', '穿搭/机位入口'],
    datasets: ['trips', 'outfits', 'cameraSpots'],
    statusKeys: ['generation', 'save'],
    actions: [
      { label: '查看穿搭详情', modal: 'outfitDetail', status: 'generation' },
      { label: '查看机位详情', modal: 'cameraSpot', status: 'generation' },
      { label: '标记保存完成', modal: 'shareCommunity', status: 'save' },
    ],
  },
  tripDetail: {
    title: '行程详情页',
    summary: '面向查看、执行、收藏与分享到社区。',
    modules: ['行程摘要', '预算与天气', '机位亮点', '分享 CTA'],
    datasets: ['trips', 'cameraSpots'],
    statusKeys: ['save', 'publish'],
    actions: [
      { label: '查看机位亮点', modal: 'cameraSpot', status: 'save' },
      { label: '分享到社区', modal: 'shareCommunity', status: 'publish' },
    ],
  },
  import: {
    title: '导入行程页',
    summary: '承接外部链接/文档导入到解析确认与补全行程。',
    modules: ['粘贴链接', '上传文档', '解析摘要', '补全预算与时长'],
    datasets: ['trips'],
    statusKeys: ['import'],
    actions: [
      { label: '确认解析结果', modal: 'importConfirm', status: 'import' },
    ],
  },
  discover: {
    title: '推荐页',
    summary: '基于热门标签与路线内容提供灵感扩展入口。',
    modules: ['标签筛选', '推荐路线卡片', '同款规划入口', '快速开始 CTA'],
    datasets: ['destinations', 'plans'],
    statusKeys: ['generation'],
    actions: [
      { label: '快速开始同款规划', modal: 'tripBrief', status: 'generation' },
    ],
  },
  community: {
    title: '社区页',
    summary: '承接内容浏览、收藏和引用行程发布。',
    modules: ['帖子流', '标签筛选', '内容详情承接', '引用行程发布'],
    datasets: ['communityPosts'],
    statusKeys: ['publish'],
    actions: [
      { label: '发布社区内容', modal: 'publishCommunity', status: 'publish' },
    ],
  },
  communityDetail: {
    title: '社区详情 / 同款规划页',
    summary: '展示帖子细节并预填开始行程，引导进入主路径。',
    modules: ['帖子详情', '预算摘要', '机位亮点', '同款规划 CTA'],
    datasets: ['communityPosts', 'trips'],
    statusKeys: ['generation', 'publish'],
    actions: [
      { label: '打开同款规划浮层', modal: 'tripBrief', status: 'generation' },
      { label: '分享灵感到社区', modal: 'shareCommunity', status: 'publish' },
    ],
  },
  myTrips: {
    title: '我的行程页',
    summary: '管理草稿、已完成行程、收藏和导入记录。',
    modules: ['草稿列表', '已完成行程', '导入记录', '删除与分享'],
    datasets: ['trips'],
    statusKeys: ['delete', 'save', 'publish'],
    actions: [
      { label: '删除行程', modal: 'deleteConfirm', status: 'delete' },
      { label: '分享到社区', modal: 'shareCommunity', status: 'publish' },
    ],
  },
}
