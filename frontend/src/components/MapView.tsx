/**
 * 地图组件
 * 通过动态 script 标签加载高德地图 JS SDK，标记所有 points
 * 无 VITE_AMAP_KEY 时显示降级占位
 */

import { useEffect, useRef, useState } from 'react'

/** 高德地图点位 */
export interface MapPoint {
  name: string
  latitude: number
  longitude: number
}

interface MapViewProps {
  points: MapPoint[]
  center?: { lat: number; lng: number }
  height?: number
}

/** 高德 SDK 最小类型声明（避免 any） */
interface AMapMarker {
  setMap: (m: unknown) => void
}
interface AMapMap {
  destroy: () => void
  setFitView: () => void
}
interface AMapConstructor {
  Map: new (el: HTMLElement, opts: Record<string, unknown>) => AMapMap
  Marker: new (opts: Record<string, unknown>) => AMapMarker
}
interface AMapGlobal {
  AMap: AMapConstructor
  _AMapSecurityConfig?: {
    securityJsCode?: string
  }
}

/** 动态加载高德 SDK（带去重） */
let amapLoader: Promise<AMapConstructor | null> | null = null
function loadAmap(key: string, securityJsCode?: string): Promise<AMapConstructor | null> {
  if (amapLoader) return amapLoader
  amapLoader = new Promise((resolve) => {
    const existing = document.querySelector<HTMLScriptElement>(
      'script[data-amap-sdk]',
    )
    if (existing) {
      // 已存在脚本，轮询等待 AMap 挂载
      const g = window as unknown as Partial<AMapGlobal>
      if (g.AMap) {
        resolve(g.AMap)
        return
      }
      const poll = window.setInterval(() => {
        const gg = window as unknown as Partial<AMapGlobal>
        if (gg.AMap) {
          window.clearInterval(poll)
          resolve(gg.AMap)
        }
      }, 100)
      return
    }
    if (securityJsCode) {
      const g = window as unknown as Partial<AMapGlobal>
      g._AMapSecurityConfig = { securityJsCode }
    }
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(key)}`
    script.async = true
    script.setAttribute('data-amap-sdk', 'true')
    script.onload = () => {
      const g = window as unknown as Partial<AMapGlobal>
      resolve(g.AMap ?? null)
    }
    script.onerror = () => resolve(null)
    document.head.appendChild(script)
  })
  return amapLoader
}

export function MapView({ points, center, height = 360 }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<AMapMap | null>(null)
  const markersRef = useRef<AMapMarker[]>([])
  const [status, setStatus] = useState<'loading' | 'ready' | 'no-key' | 'error'>(
    'loading',
  )

  const key = import.meta.env.VITE_AMAP_KEY
  const securityJsCode = import.meta.env.VITE_AMAP_SECURITY_JS_CODE

  useEffect(() => {
    if (!key) {
      setStatus('no-key')
      return
    }
    let cancelled = false

    void loadAmap(key, securityJsCode).then((AMap) => {
      if (cancelled || !AMap || !containerRef.current) {
        if (!cancelled) setStatus(AMap ? 'error' : 'no-key')
        return
      }
      try {
        // 计算中心点
        const hasCenter = center && typeof center.lat === 'number' && typeof center.lng === 'number'
        const cLng = hasCenter ? center!.lng : points[0]?.longitude ?? 116.397
        const cLat = hasCenter ? center!.lat : points[0]?.latitude ?? 39.908

        const map = new AMap.Map(containerRef.current, {
          zoom: 12,
          center: [cLng, cLat],
          viewMode: '2D',
        })
        mapInstanceRef.current = map

        // 清理旧标记
        for (const m of markersRef.current) m.setMap(null)
        markersRef.current = []

        // 添加新标记
        for (const p of points) {
          if (typeof p.latitude !== 'number' || typeof p.longitude !== 'number') continue
          const marker = new AMap.Marker({
            position: [p.longitude, p.latitude],
            title: p.name,
          })
          marker.setMap(map)
          markersRef.current.push(marker)
        }

        // 自动调整视野以包含所有标记
        if (points.length > 1) {
          map.setFitView()
        }

        setStatus('ready')
      } catch {
        setStatus('error')
      }
    })

    return () => {
      cancelled = true
      for (const m of markersRef.current) m.setMap(null)
      markersRef.current = []
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.destroy()
        } catch {
          /* noop */
        }
        mapInstanceRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  // points 变化时刷新标记
  useEffect(() => {
    if (status !== 'ready') return
    const g = window as unknown as Partial<AMapGlobal>
    const AMap = g.AMap
    const map = mapInstanceRef.current
    if (!AMap || !map) return
    for (const m of markersRef.current) m.setMap(null)
    markersRef.current = []
    for (const p of points) {
      if (typeof p.latitude !== 'number' || typeof p.longitude !== 'number') continue
      const marker = new AMap.Marker({
        position: [p.longitude, p.latitude],
        title: p.name,
      })
      marker.setMap(map)
      markersRef.current.push(marker)
    }
    if (points.length > 1) {
      map.setFitView()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points])

  const fallbackPoints = points
    .filter((p) => typeof p.latitude === 'number' && typeof p.longitude === 'number')
    .slice(0, 6)

  if (status === 'no-key' || status === 'error') {
    return (
      <div
        style={{
          height,
          display: 'flex',
          alignItems: 'stretch',
          justifyContent: 'space-between',
          flexDirection: 'column',
          gap: '14px',
          borderRadius: '12px',
          border: '1px solid var(--border)',
          background: 'linear-gradient(135deg, var(--surface-elevated), var(--surface-subtle))',
          color: 'var(--ink-secondary)',
          padding: '18px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontSize: '1.4rem' }}>🗺️</span>
            <strong style={{ color: 'var(--ink)', fontSize: '0.95rem' }}>
              {status === 'no-key' ? '地图服务待启用' : '地图加载失败'}
            </strong>
          </div>
          <p style={{ fontSize: '0.78rem', lineHeight: 1.5, margin: 0 }}>
            {status === 'no-key'
              ? '当前环境未启用高德交互地图，因此先展示路线点位清单；启用地图服务后会自动切换为可缩放、可拖拽的地图。'
              : '暂时无法加载交互地图，你仍可先按下方点位核对路线。'}
          </p>
        </div>
        {fallbackPoints.length > 0 && (
          <div style={{ display: 'grid', gap: '8px', overflow: 'auto' }}>
            {fallbackPoints.map((p, index) => (
              <div
                key={`${p.name}-${p.latitude}-${p.longitude}`}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '28px 1fr',
                  gap: '10px',
                  alignItems: 'center',
                  padding: '10px 12px',
                  borderRadius: '10px',
                  background: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                }}
              >
                <span
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '999px',
                    background: 'var(--brand)',
                    color: '#fff',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                  }}
                >
                  {index + 1}
                </span>
                <div>
                  <div style={{ color: 'var(--ink)', fontWeight: 700, fontSize: '0.82rem' }}>
                    {p.name}
                  </div>
                  <div style={{ color: 'var(--ink-tertiary)', fontSize: '0.7rem' }}>
                    {p.latitude.toFixed(5)}, {p.longitude.toFixed(5)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height,
        borderRadius: '12px',
        overflow: 'hidden',
        border: '1px solid var(--border)',
      }}
    />
  )
}

export default MapView
