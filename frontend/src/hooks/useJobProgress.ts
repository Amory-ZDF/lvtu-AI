/**
 * useJobProgress
 * 通过 SSE 订阅异步任务进度，返回实时 progress / status / outputData / error
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { streamJobProgress } from '@/services/job'
import type { JobStatus } from '@/types'

export interface UseJobProgressReturn {
  progress: number
  status: JobStatus | 'idle'
  outputData: Record<string, unknown> | null
  error: string | null
  start: (jobId: string) => void
  reset: () => void
}

/** 从 SSE 事件 data 中安全提取数值 */
function num(v: unknown): number | null {
  return typeof v === 'number' && Number.isFinite(v) ? v : null
}

/** 从 SSE 事件 data 中安全提取字符串 */
function str(v: unknown): string | null {
  return typeof v === 'string' ? v : null
}

export function useJobProgress(): UseJobProgressReturn {
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<JobStatus | 'idle'>('idle')
  const [outputData, setOutputData] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const unsubscribeRef = useRef<(() => void) | null>(null)

  const cleanup = useCallback(() => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
      unsubscribeRef.current = null
    }
  }, [])

  const reset = useCallback(() => {
    cleanup()
    setProgress(0)
    setStatus('idle')
    setOutputData(null)
    setError(null)
  }, [cleanup])

  const start = useCallback(
    (jobId: string) => {
      cleanup()
      setError(null)
      setProgress(0)
      setStatus('pending')
      setOutputData(null)

      unsubscribeRef.current = streamJobProgress(jobId, {
        onProgress: (data) => {
          const p = num(data.progress)
          const s = str(data.status) as JobStatus | null
          if (p !== null) setProgress(Math.max(0, Math.min(100, p)))
          if (s) setStatus(s)
          // 部分实现会在 progress 事件里携带 output_data
          if (data.output_data && typeof data.output_data === 'object') {
            setOutputData(data.output_data as Record<string, unknown>)
          }
        },
        onComplete: (data) => {
          setProgress(100)
          setStatus('succeeded')
          if (data && typeof data === 'object') {
            // complete 事件的数据结构为 {job_id, status, output_data, ...}
            // 需要提取 output_data 作为业务数据
            const raw = data as Record<string, unknown>
            const output = raw.output_data
            setOutputData(
              output && typeof output === 'object'
                ? (output as Record<string, unknown>)
                : raw,
            )
          }
        },
        onError: (err) => {
          setStatus('failed')
          setError(err.message || '任务执行失败')
        },
      })
    },
    [cleanup],
  )

  // 卸载时关闭订阅
  useEffect(() => {
    return () => {
      cleanup()
    }
  }, [cleanup])

  return { progress, status, outputData, error, start, reset }
}

export default useJobProgress
