/**
 * 行程调整服务（自然语言改写）
 * 与后端 `app/api/v1/adjustments.py` 对齐
 */

import { apiClient } from './api'
import type { AdjustmentRequest, GenerationJob } from '@/types'

/**
 * 自然语言改写行程
 * POST /trips/{trip_id}/adjustments
 * 返回 {job_id, status, output_data}
 */
export function createAdjustment(
  tripId: string,
  payload: AdjustmentRequest,
): Promise<GenerationJob> {
  return apiClient.post<GenerationJob>(`/trips/${tripId}/adjustments`, payload)
}

export const adjustmentService = {
  createAdjustment,
}

export default adjustmentService
