/**
 * E2E 测试共享 Mock 数据与 API 拦截辅助
 * - 所有后端 API 请求通过 page.route 拦截并返回 mock 数据
 * - 测试无需真实后端即可通过
 * - setupApiMocks 每次调用都会创建独立的可变状态（避免测试间污染）
 */
import type { Page } from '@playwright/test'

/** 统一响应时间戳 */
const NOW = '2026-03-01T00:00:00.000Z'

/** 列表分页 meta */
function listMeta(total: number) {
  return { page: 1, page_size: 20, total, has_more: false }
}

/** 包裹为统一响应格式 { success, data, meta } */
function wrap<T>(data: T) {
  return {
    success: true as const,
    data,
    meta: { request_id: 'mock-req', timestamp: NOW },
  }
}

// ── Mock 数据 ──

export const mockUser = {
  id: 'user-1',
  email: 'test@lv.com',
  username: 'tester',
  display_name: '测试用户',
  avatar_url: null,
  bio: null,
  created_at: NOW,
  updated_at: NOW,
  preference: null,
}

export const mockToken = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
  expires_in: 3600,
}

export const mockTrip = {
  id: 'trip-1',
  user_id: 'user-1',
  title: '厦门 · 文艺海岸 3 日游',
  destination_name: '厦门',
  start_date: '2026-03-15',
  end_date: '2026-03-17',
  status: 'upcoming' as const,
  cover_image_url: null,
  notes: '记得带防晒霜',
  created_at: NOW,
  updated_at: NOW,
}

export const mockTripDays = [
  {
    id: 'day-1',
    trip_id: 'trip-1',
    day_index: 1,
    date: '2026-03-15',
    title: '抵达厦门',
    summary: '环岛路 + 中山路步行街',
    created_at: NOW,
    updated_at: NOW,
  },
  {
    id: 'day-2',
    trip_id: 'trip-1',
    day_index: 2,
    date: '2026-03-16',
    title: '鼓浪屿一日',
    summary: '钢琴码头 + 日光岩',
    created_at: NOW,
    updated_at: NOW,
  },
]

export const mockTripPoints = {
  'day-1': [
    {
      id: 'point-1',
      trip_day_id: 'day-1',
      name: '环岛路骑行',
      point_type: 'spot' as const,
      address: '厦门环岛路',
      latitude: 24.44,
      longitude: 118.12,
      start_time: '09:00:00',
      end_time: '11:00:00',
      sort_order: 0,
      notes: '海边骑行，注意防晒',
      image_url: null,
      created_at: NOW,
      updated_at: NOW,
    },
  ],
  'day-2': [] as unknown[],
}

export const mockPackingItems = [
  {
    id: 'pack-1',
    trip_id: 'trip-1',
    name: '护照',
    category: '证件',
    quantity: 1,
    is_checked: false,
    note: null,
    created_at: NOW,
    updated_at: NOW,
  },
  {
    id: 'pack-2',
    trip_id: 'trip-1',
    name: 'T恤',
    category: '衣物',
    quantity: 3,
    is_checked: false,
    note: null,
    created_at: NOW,
    updated_at: NOW,
  },
]

export const mockOutfits = [
  {
    id: 'outfit-1',
    trip_id: 'trip-1',
    scene: '海边',
    season: '春',
    style: '清新文艺风',
    items: [{ name: '白衬衫' }, { name: '牛仔半裙' }],
    tips: '注意防晒，搭配草帽',
    images: [] as string[],
    created_at: NOW,
    updated_at: NOW,
  },
]

export const mockSpots = [
  {
    id: 'spot-1',
    trip_id: 'trip-1',
    trip_point_id: null,
    name: '环岛路观景台',
    location: '厦门环岛路',
    composition: '低角度仰拍海平面，利用礁石做前景',
    best_time: '日出 / 日落',
    photo_score: 92,
    tips: '逆光剪影效果佳',
    images: [] as string[],
    created_at: NOW,
    updated_at: NOW,
  },
]

export const mockDestinations = {
  query_summary: '基于你的偏好生成 2 个目的地',
  destinations: [
    {
      id: 'dest-1',
      name: '厦门',
      country_or_region: '福建',
      match_score: 92,
      budget_range: '3000-5000 元',
      best_season: '春秋',
      vibe_tags: ['文艺', '海边', '拍照'],
      reasons: ['文艺小镇适合拍照', '海鲜美食丰富', '交通便利'],
      hero_image: {
        category: 'city',
        url: '',
        thumbnail_url: '',
        alt: '厦门',
        provider: 'mock',
        placeholder: true,
      },
      gallery: [],
    },
    {
      id: 'dest-2',
      name: '大理',
      country_or_region: '云南',
      match_score: 86,
      budget_range: '3000-5000 元',
      best_season: '春秋',
      vibe_tags: ['人文', '户外', '疗愈'],
      reasons: ['苍山洱海风光', '白族人文浓郁'],
      hero_image: {
        category: 'city',
        url: '',
        thumbnail_url: '',
        alt: '大理',
        provider: 'mock',
        placeholder: true,
      },
      gallery: [],
    },
  ],
}

export const mockRouteOptions = {
  destination_name: '厦门',
  options: [
    {
      id: 'opt-a',
      title: '文艺海岸慢游',
      pace: '慢节奏 · 深度',
      estimated_budget: '3500 元',
      photo_score: 88,
      summary: '环岛路 + 鼓浪屿 + 曾厝垵，深度体验文艺海岸线',
      days: [],
    },
    {
      id: 'opt-b',
      title: '打卡精华快线',
      pace: '紧凑 · 多打卡',
      estimated_budget: '4200 元',
      photo_score: 82,
      summary: '精华景点全覆盖，适合短途高效打卡',
      days: [],
    },
  ],
}


/** SSE 进度流 body：先发 progress 事件，再发 complete 事件携带目的地结果 */
function buildDestinationsSseBody(): string {
  return (
    `event: progress\ndata: ${JSON.stringify({ progress: 50, status: 'running' })}\n\n` +
    `event: complete\ndata: ${JSON.stringify(mockDestinations)}\n\n`
  )
}

/**
 * 注册全部 API mock。每次调用产生独立可变状态。
 * 返回一个可手动触发"下一份推荐结果"的句柄（此处未使用，预留扩展）。
 */
export async function setupApiMocks(page: Page): Promise<void> {
  // 可变状态（每个测试独立）
  const packingItems = mockPackingItems.map((i) => ({ ...i }))
  const pointsByDay: Record<string, unknown[]> = {
    'day-1': mockTripPoints['day-1'].map((p) => ({ ...(p as object) })),
    'day-2': [],
  }
  let idSeq = 100

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request()
    const method = request.method()
    const url = new URL(request.url())
    const apiPath = url.pathname.replace('/api/v1', '')
    const body = request.postDataJSON?.() ?? undefined

    // ── 鉴权 ──
    if (apiPath === '/auth/login' && method === 'POST') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(wrap({ token: mockToken, user: mockUser })),
      })
    }
    if (apiPath === '/auth/register' && method === 'POST') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(wrap({ token: mockToken, user: mockUser })),
      })
    }
    if (apiPath === '/auth/me' && method === 'GET') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(wrap(mockUser)),
      })
    }

    // ── AI 规划 ──
    if (apiPath === '/planning/destinations/async' && method === 'POST') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          wrap({
            job_id: 'job-dest-1',
            job_type: 'destination_recommendation',
            status: 'pending',
            progress: 0,
            user_id: 'user-1',
            input_data: {},
            output_data: null,
            error_message: null,
            created_at: NOW,
            updated_at: NOW,
            started_at: null,
            completed_at: null,
          }),
        ),
      })
    }
    if (apiPath === '/planning/destinations' && method === 'POST') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(wrap(mockDestinations)),
      })
    }
    if (apiPath === '/planning/routes' && method === 'POST') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(wrap(mockRouteOptions)),
      })
    }

    // ── SSE 任务进度流 ──
    if (/^\/jobs\/[^/]+\/stream$/.test(apiPath) && method === 'GET') {
      return route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: buildDestinationsSseBody(),
      })
    }

    // ── 行程 CRUD ──
    if (/^\/users\/[^/]+\/trips$/.test(apiPath)) {
      if (method === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(wrap({ items: [mockTrip], meta: listMeta(1) })),
        })
      }
      if (method === 'POST') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(wrap(mockTrip)),
        })
      }
    }
    if (/^\/users\/[^/]+\/trips\/[^/]+$/.test(apiPath) && method === 'GET') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(wrap(mockTrip)),
      })
    }

    // ── 行程天 ──
    if (/^\/trips\/[^/]+\/days$/.test(apiPath) && method === 'GET') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(wrap({ items: mockTripDays, meta: listMeta(mockTripDays.length) })),
      })
    }

    // ── 打包清单 ──
    if (/^\/trips\/[^/]+\/packing-items$/.test(apiPath)) {
      if (method === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(wrap({ items: packingItems, meta: listMeta(packingItems.length) })),
        })
      }
      if (method === 'POST') {
        const name = (body?.name as string) || '新物品'
        const category = (body?.category as string) || '其他'
        const newItem = {
          id: `pack-new-${idSeq++}`,
          trip_id: 'trip-1',
          name,
          category,
          quantity: 1,
          is_checked: false,
          note: null,
          created_at: NOW,
          updated_at: NOW,
        }
        packingItems.push(newItem)
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(wrap(newItem)),
        })
      }
    }
    if (/^\/trips\/[^/]+\/packing-items\/[^/]+\/checked$/.test(apiPath) && method === 'PATCH') {
      const isChecked = !!body?.is_checked
      const itemId = apiPath.split('/').slice(-2, -1)[0]
      const item = packingItems.find((i) => i.id === itemId)
      if (item) item.is_checked = isChecked
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(wrap(item ?? { id: itemId, is_checked: isChecked })),
      })
    }
    if (/^\/trips\/[^/]+\/packing-items\/[^/]+$/.test(apiPath) && method === 'DELETE') {
      return route.fulfill({ status: 204 })
    }

    // ── 穿搭 / 机位 ──
    if (/^\/trips\/[^/]+\/outfits$/.test(apiPath) && method === 'GET') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(wrap({ items: mockOutfits, meta: listMeta(mockOutfits.length) })),
      })
    }
    if (/^\/trips\/[^/]+\/spots$/.test(apiPath) && method === 'GET') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(wrap({ items: mockSpots, meta: listMeta(mockSpots.length) })),
      })
    }
    if (/^\/spots\/[^/]+$/.test(apiPath) && method === 'DELETE') {
      return route.fulfill({ status: 204 })
    }

    // ── 行程点 ──
    if (/^\/trip-days\/[^/]+\/points$/.test(apiPath)) {
      const dayId = apiPath.split('/')[2]
      if (method === 'GET') {
        const items = pointsByDay[dayId] ?? []
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(wrap({ items, meta: listMeta(items.length) })),
        })
      }
      if (method === 'POST') {
        const newPoint = {
          id: `point-new-${idSeq++}`,
          trip_day_id: dayId,
          name: (body?.name as string) || '新行程点',
          point_type: (body?.point_type as string) || 'other',
          address: null,
          latitude: null,
          longitude: null,
          start_time: null,
          end_time: null,
          sort_order: (body?.sort_order as number) ?? 0,
          notes: null,
          image_url: null,
          created_at: NOW,
          updated_at: NOW,
        }
        pointsByDay[dayId] = [...(pointsByDay[dayId] ?? []), newPoint]
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(wrap(newPoint)),
        })
      }
    }
    if (/^\/trip-days\/[^/]+\/points\/reorder$/.test(apiPath) && method === 'PATCH') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(wrap([])),
      })
    }
    if (/^\/trip-days\/[^/]+\/points\/[^/]+$/.test(apiPath)) {
      if (method === 'DELETE') {
        return route.fulfill({ status: 204 })
      }
      if (method === 'PATCH') {
        // 自动保存：返回一个最小可用对象即可
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(wrap({ ok: true })),
        })
      }
    }

    // ── 行程自然语言调整 ──
    if (/^\/trips\/[^/]+\/adjustments$/.test(apiPath) && method === 'POST') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          wrap({
            job_id: 'job-adj-1',
            job_type: 'trip_adjustment',
            status: 'succeeded',
            progress: 100,
            user_id: 'user-1',
            input_data: {},
            output_data: null,
            error_message: null,
            created_at: NOW,
            updated_at: NOW,
            started_at: NOW,
            completed_at: NOW,
          }),
        ),
      })
    }

    // ── 兜底：未匹配的 API 返回空列表 / 空对象，避免阻塞 ──
    if (method === 'DELETE') return route.fulfill({ status: 204 })
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(wrap({ items: [], meta: listMeta(0) })),
    })
  })
}
