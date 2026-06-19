/**
 * 行程服务
 * 与后端 `app/api/v1/core_business.py` 对齐
 * 所有响应已被 apiClient 自动解包
 */

import { apiClient, type QueryParams } from './api'
import type {
  ListResponse,
  Trip,
  TripCreate,
  TripDay,
  TripDayCreate,
  TripDayUpdate,
  TripPoint,
  TripPointCreate,
  TripPointUpdate,
  TripUpdate,
  PackingItem,
  PackingItemCreate,
  PackingItemUpdate,
  PackingItemCheckUpdate,
  SortOrderUpdate,
} from '@/types'

/** 列表查询参数 */
export interface TripListQuery {
  page?: number
  page_size?: number
}

/** 将 TripListQuery 转为 QueryParams */
function toParams(query?: TripListQuery): QueryParams | undefined {
  if (!query) return undefined
  return { page: query.page, page_size: query.page_size }
}

// ── 行程 CRUD ──

export function listTrips(userId: string, query?: TripListQuery): Promise<ListResponse<Trip>> {
  return apiClient.get<ListResponse<Trip>>(`/users/${userId}/trips`, toParams(query))
}

export function createTrip(userId: string, payload: TripCreate): Promise<Trip> {
  return apiClient.post<Trip>(`/users/${userId}/trips`, payload)
}

export function getTrip(userId: string, tripId: string): Promise<Trip> {
  return apiClient.get<Trip>(`/users/${userId}/trips/${tripId}`)
}

export function updateTrip(userId: string, tripId: string, payload: TripUpdate): Promise<Trip> {
  return apiClient.patch<Trip>(`/users/${userId}/trips/${tripId}`, payload)
}

export function deleteTrip(userId: string, tripId: string): Promise<void> {
  return apiClient.delete<void>(`/users/${userId}/trips/${tripId}`)
}

// ── 行程天 CRUD ──

export function listTripDays(tripId: string, query?: TripListQuery): Promise<ListResponse<TripDay>> {
  return apiClient.get<ListResponse<TripDay>>(`/trips/${tripId}/days`, toParams(query))
}

export function createTripDay(tripId: string, payload: TripDayCreate): Promise<TripDay> {
  return apiClient.post<TripDay>(`/trips/${tripId}/days`, payload)
}

export function reorderTripDays(tripId: string, orderedIds: string[]): Promise<TripDay[]> {
  const payload: SortOrderUpdate = { ordered_ids: orderedIds }
  return apiClient.patch<TripDay[]>(`/trips/${tripId}/days/reorder`, payload)
}

export function getTripDay(tripId: string, dayId: string): Promise<TripDay> {
  return apiClient.get<TripDay>(`/trips/${tripId}/days/${dayId}`)
}

export function updateTripDay(
  tripId: string,
  dayId: string,
  payload: TripDayUpdate,
): Promise<TripDay> {
  return apiClient.patch<TripDay>(`/trips/${tripId}/days/${dayId}`, payload)
}

export function deleteTripDay(tripId: string, dayId: string): Promise<void> {
  return apiClient.delete<void>(`/trips/${tripId}/days/${dayId}`)
}

// ── 行程点 CRUD ──

export function listTripPoints(
  tripDayId: string,
  query?: TripListQuery,
): Promise<ListResponse<TripPoint>> {
  return apiClient.get<ListResponse<TripPoint>>(`/trip-days/${tripDayId}/points`, toParams(query))
}

export function createTripPoint(tripDayId: string, payload: TripPointCreate): Promise<TripPoint> {
  return apiClient.post<TripPoint>(`/trip-days/${tripDayId}/points`, payload)
}

export function reorderTripPoints(
  tripDayId: string,
  orderedIds: string[],
): Promise<TripPoint[]> {
  const payload: SortOrderUpdate = { ordered_ids: orderedIds }
  return apiClient.patch<TripPoint[]>(`/trip-days/${tripDayId}/points/reorder`, payload)
}

export function getTripPoint(tripDayId: string, pointId: string): Promise<TripPoint> {
  return apiClient.get<TripPoint>(`/trip-days/${tripDayId}/points/${pointId}`)
}

export function updateTripPoint(
  tripDayId: string,
  pointId: string,
  payload: TripPointUpdate,
): Promise<TripPoint> {
  return apiClient.patch<TripPoint>(`/trip-days/${tripDayId}/points/${pointId}`, payload)
}

export function deleteTripPoint(tripDayId: string, pointId: string): Promise<void> {
  return apiClient.delete<void>(`/trip-days/${tripDayId}/points/${pointId}`)
}

// ── 打包清单 CRUD ──

export function listPackingItems(
  tripId: string,
  query?: TripListQuery,
): Promise<ListResponse<PackingItem>> {
  return apiClient.get<ListResponse<PackingItem>>(`/trips/${tripId}/packing-items`, toParams(query))
}

export function createPackingItem(
  tripId: string,
  payload: PackingItemCreate,
): Promise<PackingItem> {
  return apiClient.post<PackingItem>(`/trips/${tripId}/packing-items`, payload)
}

export function updatePackingItem(
  tripId: string,
  itemId: string,
  payload: PackingItemUpdate,
): Promise<PackingItem> {
  return apiClient.patch<PackingItem>(`/trips/${tripId}/packing-items/${itemId}`, payload)
}

export function checkPackingItem(
  tripId: string,
  itemId: string,
  isChecked: boolean,
): Promise<PackingItem> {
  const payload: PackingItemCheckUpdate = { is_checked: isChecked }
  return apiClient.patch<PackingItem>(
    `/trips/${tripId}/packing-items/${itemId}/checked`,
    payload,
  )
}

export function deletePackingItem(tripId: string, itemId: string): Promise<void> {
  return apiClient.delete<void>(`/trips/${tripId}/packing-items/${itemId}`)
}

export const tripService = {
  listTrips,
  createTrip,
  getTrip,
  updateTrip,
  deleteTrip,
  listTripDays,
  createTripDay,
  reorderTripDays,
  getTripDay,
  updateTripDay,
  deleteTripDay,
  listTripPoints,
  createTripPoint,
  reorderTripPoints,
  getTripPoint,
  updateTripPoint,
  deleteTripPoint,
  listPackingItems,
  createPackingItem,
  updatePackingItem,
  checkPackingItem,
  deletePackingItem,
}

export default tripService
