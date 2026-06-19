/**
 * 行程状态管理
 * - 当前行程
 * - 行程列表
 * - 行程天 / 行程点 / 打包清单 / 穿搭 / 机位
 * - 推荐结果（目的地 / 路线方案）
 * - loading / error 状态
 */

import { create } from 'zustand'
import type {
  Trip,
  TripDay,
  TripPoint,
  PackingItem,
  OutfitRecommendation,
  PhotoSpotRecommendation,
  DestinationRecommendationPayload,
  RouteGenerationPayload,
  DestinationRecommendationRequest,
  RouteGenerationRequest,
} from '@/types'
import * as tripService from '@/services/trip'
import * as outfitService from '@/services/outfit'
import * as spotService from '@/services/spot'
import * as planningService from '@/services/planning'

interface TripState {
  currentTrip: Trip | null
  trips: Trip[]
  days: TripDay[]
  /** 按 day_id 索引的行程点 */
  pointsByDay: Record<string, TripPoint[]>
  packingItems: PackingItem[]
  outfits: OutfitRecommendation[]
  spots: PhotoSpotRecommendation[]

  // 推荐结果
  destinations: DestinationRecommendationPayload | null
  routeOptions: RouteGenerationPayload | null
  /** 最近一次推荐请求参数（用于"换一批"） */
  lastRecommendRequest: DestinationRecommendationRequest | null
  /** 最近一次路线生成请求参数 */
  lastRouteRequest: RouteGenerationRequest | null

  // loading / error
  loadingTrips: boolean
  loadingTrip: boolean
  loadingDays: boolean
  loadingPacking: boolean
  loadingOutfits: boolean
  loadingSpots: boolean
  loadingDestinations: boolean
  loadingRoutes: boolean
  error: string | null

  // 基础 setter
  setCurrentTrip: (trip: Trip | null) => void
  setTrips: (trips: Trip[]) => void
  setDays: (days: TripDay[]) => void
  setPointsForDay: (dayId: string, points: TripPoint[]) => void
  setPackingItems: (items: PackingItem[]) => void
  setOutfits: (outfits: OutfitRecommendation[]) => void
  setSpots: (spots: PhotoSpotRecommendation[]) => void
  setDestinations: (data: DestinationRecommendationPayload | null) => void
  setRouteOptions: (data: RouteGenerationPayload | null) => void
  setError: (err: string | null) => void
  reset: () => void

  // 异步 actions
  fetchTrips: (userId: string) => Promise<void>
  fetchTrip: (userId: string, tripId: string) => Promise<void>
  fetchDays: (tripId: string) => Promise<void>
  fetchPointsForDay: (dayId: string) => Promise<void>
  fetchPackingItems: (tripId: string) => Promise<void>
  fetchOutfits: (tripId: string) => Promise<void>
  fetchSpots: (tripId: string) => Promise<void>
  recommendDestinations: (payload: DestinationRecommendationRequest) => Promise<void>
  generateRoutes: (payload: RouteGenerationRequest) => Promise<void>
}

export const useTripStore = create<TripState>((set) => ({
  currentTrip: null,
  trips: [],
  days: [],
  pointsByDay: {},
  packingItems: [],
  outfits: [],
  spots: [],
  destinations: null,
  routeOptions: null,
  lastRecommendRequest: null,
  lastRouteRequest: null,

  loadingTrips: false,
  loadingTrip: false,
  loadingDays: false,
  loadingPacking: false,
  loadingOutfits: false,
  loadingSpots: false,
  loadingDestinations: false,
  loadingRoutes: false,
  error: null,

  setCurrentTrip: (currentTrip) => set({ currentTrip }),
  setTrips: (trips) => set({ trips }),
  setDays: (days) => set({ days }),
  setPointsForDay: (dayId, points) =>
    set((state) => ({ pointsByDay: { ...state.pointsByDay, [dayId]: points } })),
  setPackingItems: (packingItems) => set({ packingItems }),
  setOutfits: (outfits) => set({ outfits }),
  setSpots: (spots) => set({ spots }),
  setDestinations: (destinations) => set({ destinations }),
  setRouteOptions: (routeOptions) => set({ routeOptions }),
  setError: (error) => set({ error }),

  reset: () =>
    set({
      currentTrip: null,
      days: [],
      pointsByDay: {},
      packingItems: [],
      outfits: [],
      spots: [],
      error: null,
    }),

  fetchTrips: async (userId) => {
    set({ loadingTrips: true, error: null })
    try {
      const res = await tripService.listTrips(userId)
      set({ trips: res.items, loadingTrips: false })
    } catch (err) {
      set({
        loadingTrips: false,
        error: err instanceof Error ? err.message : '获取行程列表失败',
      })
    }
  },

  fetchTrip: async (userId, tripId) => {
    set({ loadingTrip: true, error: null })
    try {
      const trip = await tripService.getTrip(userId, tripId)
      set({ currentTrip: trip, loadingTrip: false })
    } catch (err) {
      set({
        loadingTrip: false,
        error: err instanceof Error ? err.message : '获取行程详情失败',
      })
    }
  },

  fetchDays: async (tripId) => {
    set({ loadingDays: true, error: null })
    try {
      const res = await tripService.listTripDays(tripId)
      set({ days: res.items, loadingDays: false })
    } catch (err) {
      set({
        loadingDays: false,
        error: err instanceof Error ? err.message : '获取行程天失败',
      })
    }
  },

  fetchPointsForDay: async (dayId) => {
    try {
      const res = await tripService.listTripPoints(dayId)
      set((state) => ({ pointsByDay: { ...state.pointsByDay, [dayId]: res.items } }))
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取行程点失败' })
    }
  },

  fetchPackingItems: async (tripId) => {
    set({ loadingPacking: true, error: null })
    try {
      const res = await tripService.listPackingItems(tripId)
      set({ packingItems: res.items, loadingPacking: false })
    } catch (err) {
      set({
        loadingPacking: false,
        error: err instanceof Error ? err.message : '获取打包清单失败',
      })
    }
  },

  fetchOutfits: async (tripId) => {
    set({ loadingOutfits: true, error: null })
    try {
      const res = await outfitService.listOutfits(tripId)
      set({ outfits: res.items, loadingOutfits: false })
    } catch (err) {
      set({
        loadingOutfits: false,
        error: err instanceof Error ? err.message : '获取穿搭推荐失败',
      })
    }
  },

  fetchSpots: async (tripId) => {
    set({ loadingSpots: true, error: null })
    try {
      const res = await spotService.listSpots(tripId)
      set({ spots: res.items, loadingSpots: false })
    } catch (err) {
      set({
        loadingSpots: false,
        error: err instanceof Error ? err.message : '获取机位推荐失败',
      })
    }
  },

  recommendDestinations: async (payload) => {
    set({ loadingDestinations: true, error: null })
    try {
      const data = await planningService.recommendDestinations(payload)
      set({
        destinations: data,
        lastRecommendRequest: payload,
        loadingDestinations: false,
      })
    } catch (err) {
      set({
        loadingDestinations: false,
        error: err instanceof Error ? err.message : '目的地推荐失败',
      })
    }
  },

  generateRoutes: async (payload) => {
    set({ loadingRoutes: true, error: null })
    try {
      const data = await planningService.generateRoutes(payload)
      set({
        routeOptions: data,
        lastRouteRequest: payload,
        loadingRoutes: false,
      })
    } catch (err) {
      set({
        loadingRoutes: false,
        error: err instanceof Error ? err.message : '路线生成失败',
      })
    }
  },
}))

export default useTripStore
