/**
 * useCollaboration
 * 连接行程协同编辑 WebSocket，提供在线用户、发送事件、自动重连
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { ACCESS_TOKEN_KEY } from '@/services/api'

/** 协作者信息 */
export interface CollaboratorUser {
  user_id: string
  display_name?: string
  avatar_url?: string | null
}

export interface UseCollaborationOptions {
  onRemoteEdit?: (userId: string, payload: unknown) => void
  onRemoteCursor?: (userId: string, position: unknown) => void
}

export interface UseCollaborationReturn {
  onlineUsers: CollaboratorUser[]
  connected: boolean
  sendCursorMove: (position: unknown) => void
  sendEdit: (payload: unknown) => void
  sendLock: (module: string) => void
}

/** 根据 API base URL 构造 WebSocket 地址 */
function buildWsUrl(tripId: string): string {
  const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  if (/^https?:\/\//.test(apiBase)) {
    return `${apiBase.replace(/^http/, 'ws')}/ws/trips/${tripId}`
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}${apiBase}/ws/trips/${tripId}`
}

/** 安全读取对象字段 */
function readObj(v: unknown): Record<string, unknown> | null {
  return typeof v === 'object' && v !== null ? (v as Record<string, unknown>) : null
}

function readStr(v: unknown): string | null {
  return typeof v === 'string' ? v : null
}

export function useCollaboration(
  tripId: string,
  options?: UseCollaborationOptions,
): UseCollaborationReturn {
  const [onlineUsers, setOnlineUsers] = useState<CollaboratorUser[]>([])
  const [connected, setConnected] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const retryCountRef = useRef(0)
  const closedByUnmountRef = useRef(false)
  const optionsRef = useRef(options)

  useEffect(() => {
    optionsRef.current = options
  })

  const send = useCallback((msg: Record<string, unknown>) => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg))
    }
  }, [])

  const sendCursorMove = useCallback(
    (position: unknown) => send({ type: 'cursor_move', data: position }),
    [send],
  )
  const sendEdit = useCallback(
    (payload: unknown) => send({ type: 'edit', data: payload, module: 'itinerary' }),
    [send],
  )
  const sendLock = useCallback(
    (module: string) => send({ type: 'module_lock', module }),
    [send],
  )

  useEffect(() => {
    if (!tripId) return
    closedByUnmountRef.current = false
    let cancelled = false

    const connect = () => {
      if (cancelled || closedByUnmountRef.current) return
      const token = localStorage.getItem(ACCESS_TOKEN_KEY)
      const base = buildWsUrl(tripId)
      const url = token ? `${base}?token=${encodeURIComponent(token)}` : base
      let ws: WebSocket
      try {
        ws = new WebSocket(url)
      } catch {
        scheduleReconnect()
        return
      }
      wsRef.current = ws

      ws.onopen = () => {
        if (cancelled) return
        retryCountRef.current = 0
        setConnected(true)
      }

      ws.onclose = () => {
        if (cancelled) return
        setConnected(false)
        wsRef.current = null
        scheduleReconnect()
      }

      ws.onerror = () => {
        // onclose 会随后触发并调度重连
        try {
          ws.close()
        } catch {
          /* noop */
        }
      }

      ws.onmessage = (event) => {
        if (cancelled) return
        let data: unknown
        try {
          data = JSON.parse(event.data)
        } catch {
          return
        }
        const obj = readObj(data)
        if (!obj) return
        const type = readStr(obj.type)
        if (!type) return

        if (type === 'presence') {
          // 后端发送 online_users（UUID 字符串数组），转换为 CollaboratorUser[]
          const onlineUsers = Array.isArray(obj.online_users) ? obj.online_users : []
          const parsed: CollaboratorUser[] = []
          for (const u of onlineUsers) {
            const uid = readStr(u)
            if (!uid) continue
            parsed.push({
              user_id: uid,
              display_name: undefined,
              avatar_url: undefined,
            })
          }
          setOnlineUsers(parsed)
        } else if (type === 'edit') {
          const uid = readStr(obj.user_id)
          if (uid) optionsRef.current?.onRemoteEdit?.(uid, obj.data)
        } else if (type === 'cursor_move') {
          const uid = readStr(obj.user_id)
          if (uid) optionsRef.current?.onRemoteCursor?.(uid, obj.data)
        }
      }
    }

    const scheduleReconnect = () => {
      if (cancelled || closedByUnmountRef.current) return
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      // 指数退避，上限 30s
      const delay = Math.min(1000 * 2 ** retryCountRef.current, 30000)
      retryCountRef.current += 1
      reconnectTimerRef.current = setTimeout(() => {
        connect()
      }, delay)
    }

    connect()

    return () => {
      cancelled = true
      closedByUnmountRef.current = true
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
      if (wsRef.current) {
        try {
          wsRef.current.close()
        } catch {
          /* noop */
        }
        wsRef.current = null
      }
      setConnected(false)
      setOnlineUsers([])
    }
  }, [tripId])

  return { onlineUsers, connected, sendCursorMove, sendEdit, sendLock }
}

export default useCollaboration
