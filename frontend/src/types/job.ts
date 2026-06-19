/**
 * 生成任务类型定义
 * 与后端 `app/schemas/job.py` 对齐
 */

/** 任务状态（含后端 completed 与前端映射的 succeeded） */
export type JobStatus = 'pending' | 'running' | 'succeeded' | 'completed' | 'failed' | 'cancelled'

/** 任务类型 */
export type JobType =
  | 'destination_recommendation'
  | 'route_generation'
  | 'outfit_recommendation'
  | 'photo_spot_recommendation'
  | 'trip_adjustment'

/** 生成任务 */
export interface GenerationJob {
  job_id: string
  job_type: JobType
  status: JobStatus
  progress: number
  user_id: string | null
  input_data: Record<string, unknown>
  output_data: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  updated_at: string
  started_at: string | null
  completed_at: string | null
}

/** 任务创建请求 */
export interface JobCreateRequest {
  job_type: JobType
  input_data?: Record<string, unknown>
}

/** 行程调整请求 */
export interface AdjustmentRequest {
  instruction: string
  target_day_id?: string | null
}
