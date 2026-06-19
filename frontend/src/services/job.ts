/**
 * 任务服务
 * 与后端 `app/api/v1/jobs.py` 对齐
 */

import { apiClient, type QueryParams } from './api'
import { ACCESS_TOKEN_KEY } from './api'
import type { GenerationJob, ListResponse } from '@/types'

/** 任务列表查询参数 */
export interface JobListQuery {
  page?: number
  page_size?: number
}

/** 获取任务详情 */
export function getJob(jobId: string): Promise<GenerationJob> {
  return apiClient.get<GenerationJob>(`/jobs/${jobId}`)
}

/** 任务列表 */
export function listJobs(query?: JobListQuery): Promise<ListResponse<GenerationJob>> {
  const params: QueryParams | undefined = query
    ? { page: query.page, page_size: query.page_size }
    : undefined
  return apiClient.get<ListResponse<GenerationJob>>('/jobs', params)
}

/** SSE 事件回调 */
export interface JobStreamCallbacks {
  onProgress?: (data: Record<string, unknown>) => void
  onComplete?: (data: Record<string, unknown>) => void
  onError?: (err: Error) => void
}

/**
 * SSE 流式订阅任务进度
 * 使用 fetch + ReadableStream 解析 SSE，以支持 Authorization header
 * @returns 取消订阅函数
 */
export function streamJobProgress(jobId: string, callbacks: JobStreamCallbacks): () => void {
  const controller = new AbortController()
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  const url = `${baseURL}/jobs/${jobId}/stream`
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)

  let cancelled = false

  void (async () => {
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          Accept: 'text/event-stream',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        signal: controller.signal,
      })
      if (!response.ok || !response.body) {
        throw new Error(`SSE 连接失败 (${response.status})`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (!cancelled) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        // SSE 事件以空行分隔
        const blocks = buffer.split('\n\n')
        buffer = blocks.pop() || ''

        for (const block of blocks) {
          const event = parseSseBlock(block)
          if (!event) continue
          if (event.event === 'progress') {
            callbacks.onProgress?.(event.data)
          } else if (event.event === 'complete') {
            callbacks.onComplete?.(event.data)
            return
          }
        }
      }
    } catch (err) {
      if (cancelled) return
      callbacks.onError?.(err instanceof Error ? err : new Error('SSE 订阅失败'))
    }
  })()

  return () => {
    cancelled = true
    controller.abort()
  }
}

/** 解析单个 SSE 事件块 */
function parseSseBlock(block: string): { event: string; data: Record<string, unknown> } | null {
  let event = 'message'
  let dataStr = ''
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataStr += line.slice(5).trim()
    }
  }
  if (!dataStr) return null
  try {
    return { event, data: JSON.parse(dataStr) }
  } catch {
    return { event, data: { raw: dataStr } }
  }
}

export const jobService = {
  getJob,
  listJobs,
  streamJobProgress,
}

export default jobService
