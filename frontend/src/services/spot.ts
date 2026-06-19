/**
 * 机位推荐服务
 * 与后端 `app/api/v1/spots.py` 对齐
 */

import { apiClient, type QueryParams } from './api'
import type {
  PhotoSpotRecommendation,
  PhotoSpotRecommendationCreate,
  PhotoSpotRecommendationUpdate,
  ListResponse,
} from '@/types'

export interface SpotListQuery {
  page?: number
  page_size?: number
}

function toParams(query?: SpotListQuery): QueryParams | undefined {
  if (!query) return undefined
  return { page: query.page, page_size: query.page_size }
}

export function listSpots(
  tripId: string,
  query?: SpotListQuery,
): Promise<ListResponse<PhotoSpotRecommendation>> {
  return apiClient.get<ListResponse<PhotoSpotRecommendation>>(
    `/trips/${tripId}/spots`,
    toParams(query),
  )
}

export function createSpot(
  tripId: string,
  payload: PhotoSpotRecommendationCreate,
): Promise<PhotoSpotRecommendation> {
  return apiClient.post<PhotoSpotRecommendation>(`/trips/${tripId}/spots`, payload)
}

export function getSpot(spotId: string): Promise<PhotoSpotRecommendation> {
  return apiClient.get<PhotoSpotRecommendation>(`/spots/${spotId}`)
}

export function updateSpot(
  spotId: string,
  payload: PhotoSpotRecommendationUpdate,
): Promise<PhotoSpotRecommendation> {
  return apiClient.patch<PhotoSpotRecommendation>(`/spots/${spotId}`, payload)
}

export function deleteSpot(spotId: string): Promise<void> {
  return apiClient.delete<void>(`/spots/${spotId}`)
}

export const spotService = {
  listSpots,
  createSpot,
  getSpot,
  updateSpot,
  deleteSpot,
}

export default spotService
