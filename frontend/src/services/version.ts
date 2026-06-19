/**
 * 版本快照服务
 * 与后端 `app/api/v1/versions.py` 对齐
 */

import { apiClient, type QueryParams } from './api'
import type { ListResponse, Trip } from '@/types'

/** 版本快照 */
export interface TripVersion {
  id: string
  trip_id: string
  version_number: number
  note: string | null
  snapshot: Record<string, unknown>
  created_at: string
}

export interface VersionListQuery {
  page?: number
  page_size?: number
}

export interface VersionCreate {
  note?: string | null
}

function toParams(query?: VersionListQuery): QueryParams | undefined {
  if (!query) return undefined
  return { page: query.page, page_size: query.page_size }
}

export function listVersions(
  tripId: string,
  query?: VersionListQuery,
): Promise<ListResponse<TripVersion>> {
  return apiClient.get<ListResponse<TripVersion>>(`/trips/${tripId}/versions`, toParams(query))
}

export function createVersion(tripId: string, payload: VersionCreate): Promise<TripVersion> {
  return apiClient.post<TripVersion>(`/trips/${tripId}/versions`, undefined, {
    query: { note: payload.note ?? undefined },
  })
}

export function restoreVersion(tripId: string, versionId: string): Promise<Trip> {
  return apiClient.post<Trip>(`/trips/${tripId}/versions/${versionId}/restore`)
}

export const versionService = {
  listVersions,
  createVersion,
  restoreVersion,
}

export default versionService
