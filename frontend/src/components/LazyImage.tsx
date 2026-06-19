/**
 * 懒加载图片组件
 * - 优先使用原生 loading="lazy"
 * - IntersectionObserver 降级（老浏览器 / 强制可见控制）
 * - 支持 srcset 响应式图片
 * - 加载失败显示占位
 */

import {
  useEffect,
  useRef,
  useState,
  type ImgHTMLAttributes,
  type CSSProperties,
} from 'react'

export interface LazyImageProps
  extends Omit<ImgHTMLAttributes<HTMLImageElement>, 'loading'> {
  /** 响应式图片源集合 */
  srcset?: string
  /** 响应式图片尺寸提示 */
  sizes?: string
  /** 宽度 */
  width?: number | string
  /** 高度 */
  height?: number | string
  /** 占位背景色 / 渐变（加载中显示） */
  placeholder?: string
  /** 圆角 */
  radius?: number | string
  /** 自定义容器样式 */
  containerStyle?: CSSProperties
  /** 是否强制使用 IntersectionObserver（默认 false，优先原生 lazy） */
  forceObserver?: boolean
}

/** 检测原生 loading="lazy" 支持 */
const supportsNativeLazy =
  typeof HTMLImageElement !== 'undefined' && 'loading' in HTMLImageElement.prototype

export function LazyImage({
  src,
  srcset,
  sizes,
  alt = '',
  width,
  height,
  placeholder = 'var(--surface-subtle, #f5f5f5)',
  radius,
  containerStyle,
  forceObserver = false,
  style,
  ...rest
}: LazyImageProps) {
  const ref = useRef<HTMLImageElement | null>(null)
  const [visible, setVisible] = useState<boolean>(false)
  const [loaded, setLoaded] = useState<boolean>(false)
  const [errored, setErrored] = useState<boolean>(false)

  // 仅在不支持原生 lazy 或强制 observer 时启用观察
  const useObserver = forceObserver || !supportsNativeLazy

  useEffect(() => {
    if (!useObserver) return
    const el = ref.current
    if (!el) return
    // 已可见则跳过
    if (visible) return
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisible(true)
            observer.disconnect()
          }
        })
      },
      { rootMargin: '200px' },
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [useObserver, visible])

  const showSrc = useObserver ? (visible ? src : undefined) : src
  const showSrcset = useObserver ? (visible ? srcset : undefined) : srcset

  const wrapperStyle: CSSProperties = {
    position: 'relative',
    width: width ?? '100%',
    height: height ?? 'auto',
    background: placeholder,
    borderRadius: radius,
    overflow: 'hidden',
    ...containerStyle,
  }

  const imgStyle: CSSProperties = {
    display: loaded ? 'block' : 'none',
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    ...style,
  }

  return (
    <div style={wrapperStyle}>
      {/* 加载中骨架 */}
      {!loaded && !errored && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: placeholder,
          }}
          aria-hidden="true"
        />
      )}
      {/* 加载失败占位 */}
      {errored && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--ink-tertiary, #999)',
            fontSize: '0.85rem',
            background: placeholder,
          }}
          aria-hidden="true"
        >
          图片加载失败
        </div>
      )}
      <img
        ref={ref}
        src={showSrc}
        srcSet={showSrcset}
        sizes={sizes}
        alt={alt}
        width={width}
        height={height}
        loading="lazy"
        decoding="async"
        style={imgStyle}
        onLoad={() => setLoaded(true)}
        onError={() => setErrored(true)}
        {...rest}
      />
    </div>
  )
}

export default LazyImage
