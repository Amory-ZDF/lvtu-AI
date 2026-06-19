/**
 * useAutoSave
 * 监听 value 变化，debounce 后自动调用 saveFn
 * 通过引用相等判断是否需要保存，避免重复保存
 */

import { useCallback, useEffect, useRef, useState } from 'react'

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

export interface UseAutoSaveReturn {
  status: SaveStatus
  save: () => Promise<void>
}

export function useAutoSave<T>(
  value: T,
  saveFn: (value: T) => Promise<void>,
  delay = 1500,
): UseAutoSaveReturn {
  const [status, setStatus] = useState<SaveStatus>('idle')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const valueRef = useRef<T>(value)
  const saveFnRef = useRef(saveFn)
  const lastSavedRef = useRef<T>(value)
  const mountedRef = useRef(false)

  // 始终保持 ref 最新
  useEffect(() => {
    valueRef.current = value
    saveFnRef.current = saveFn
  })

  const save = useCallback(async () => {
    setStatus('saving')
    try {
      await saveFnRef.current(valueRef.current)
      lastSavedRef.current = valueRef.current
      setStatus('saved')
    } catch {
      setStatus('error')
    }
  }, [])

  useEffect(() => {
    // 首次挂载不触发保存
    if (!mountedRef.current) {
      mountedRef.current = true
      lastSavedRef.current = value
      return
    }
    // 值未变化（引用相等）则跳过
    if (Object.is(value, lastSavedRef.current)) return

    setStatus('saving')
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      void save()
    }, delay)

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, delay])

  // 卸载清理
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  return { status, save }
}

export default useAutoSave
