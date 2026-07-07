/**
 * 穿搭推荐服务
 * 与后端 `app/api/v1/outfits.py` 对齐
 */

import { apiClient, type QueryParams } from './api'
import type {
  OutfitRecommendation,
  OutfitRecommendationCreate,
  OutfitPreviewImageResult,
  OutfitRecommendationUpdate,
  ListResponse,
} from '@/types'

export interface OutfitListQuery {
  page?: number
  page_size?: number
}

function toParams(query?: OutfitListQuery): QueryParams | undefined {
  if (!query) return undefined
  return { page: query.page, page_size: query.page_size }
}

export function listOutfits(
  tripId: string,
  query?: OutfitListQuery,
): Promise<ListResponse<OutfitRecommendation>> {
  return apiClient.get<ListResponse<OutfitRecommendation>>(
    `/trips/${tripId}/outfits`,
    toParams(query),
  )
}

export function createOutfit(
  tripId: string,
  payload: OutfitRecommendationCreate,
): Promise<OutfitRecommendation> {
  return apiClient.post<OutfitRecommendation>(`/trips/${tripId}/outfits`, payload)
}

export function getOutfit(outfitId: string): Promise<OutfitRecommendation> {
  return apiClient.get<OutfitRecommendation>(`/outfits/${outfitId}`)
}

export function updateOutfit(
  outfitId: string,
  payload: OutfitRecommendationUpdate,
): Promise<OutfitRecommendation> {
  return apiClient.patch<OutfitRecommendation>(`/outfits/${outfitId}`, payload)
}

export function generateOutfitPreviewImage(
  outfitId: string,
  force = true,
): Promise<OutfitPreviewImageResult> {
  return apiClient.post<OutfitPreviewImageResult>(
    `/outfits/${outfitId}/preview-image`,
    { force },
  )
}

export function deleteOutfit(outfitId: string): Promise<void> {
  return apiClient.delete<void>(`/outfits/${outfitId}`)
}

export const outfitService = {
  listOutfits,
  createOutfit,
  getOutfit,
  updateOutfit,
  generateOutfitPreviewImage,
  deleteOutfit,
}

export default outfitService
