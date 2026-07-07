/**
 * AI 规划服务
 * 与后端 `app/api/v1/planning.py` 对齐
 */

import { apiClient } from './api'
import type {
  DestinationRecommendationRequest,
  DestinationRecommendationPayload,
  DestinationWeatherPayload,
  RouteGenerationRequest,
  RouteGenerationPayload,
  GenerationJob,
} from '@/types'

/** 同步目的地推荐 */
export function recommendDestinations(
  payload: DestinationRecommendationRequest,
): Promise<DestinationRecommendationPayload> {
  return apiClient.post<DestinationRecommendationPayload>('/planning/destinations', payload)
}

/** 同步路线生成 */
export function generateRoutes(payload: RouteGenerationRequest): Promise<RouteGenerationPayload> {
  return apiClient.post<RouteGenerationPayload>('/planning/routes', payload)
}

/** 目的地实时天气 */
export function getDestinationWeather(destinationName: string): Promise<DestinationWeatherPayload> {
  return apiClient.get<DestinationWeatherPayload>('/planning/weather', {
    destination_name: destinationName,
  })
}

/** 异步目的地推荐 → {job_id, status, output_data} */
export function recommendDestinationsAsync(
  payload: DestinationRecommendationRequest,
): Promise<GenerationJob> {
  return apiClient.post<GenerationJob>('/planning/destinations/async', payload)
}

/** 异步路线生成 → {job_id, status, output_data} */
export function generateRoutesAsync(payload: RouteGenerationRequest): Promise<GenerationJob> {
  return apiClient.post<GenerationJob>('/planning/routes/async', payload)
}

export const planningService = {
  recommendDestinations,
  generateRoutes,
  getDestinationWeather,
  recommendDestinationsAsync,
  generateRoutesAsync,
}

export default planningService
