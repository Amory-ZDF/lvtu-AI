/**
 * 图片上传组件
 * 支持点击 / 拖拽上传，预览已选图片
 * 通过 onUpload 回调返回图片 URL（后端上传接口由调用方注入）
 */

import { useRef, useState, type ChangeEvent, type DragEvent } from 'react'

interface ImageUploaderProps {
  onUpload: (file: File) => Promise<string>
  value?: string | null
  onChange?: (url: string | null) => void
  label?: string
  /** 上传中提示文案 */
  uploadingLabel?: string
}

export function ImageUploader({
  onUpload,
  value,
  onChange,
  label = '上传图片',
  uploadingLabel = '上传中...',
}: ImageUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(value ?? null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const handleFile = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('请选择图片文件')
      return
    }
    setError(null)
    setUploading(true)
    // 先本地预览
    const localUrl = URL.createObjectURL(file)
    setPreview(localUrl)
    try {
      const url = await onUpload(file)
      setPreview(url)
      onChange?.(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败')
      setPreview(value ?? null)
    } finally {
      setUploading(false)
    }
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) void handleFile(file)
    // 重置以便重复选择同一文件
    e.target.value = ''
  }

  const handleDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) void handleFile(file)
  }

  const handleRemove = () => {
    setPreview(null)
    setError(null)
    onChange?.(null)
  }

  return (
    <div>
      {label && (
        <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem' }}>
          {label}
        </label>
      )}
      {preview ? (
        <div
          style={{
            position: 'relative',
            width: '100%',
            height: '160px',
            borderRadius: '12px',
            overflow: 'hidden',
            background: `url(${preview}) center/cover, var(--surface-2)`,
            border: '1px solid var(--border)',
          }}
        >
          {uploading && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                background: 'rgba(0,0,0,0.4)',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.85rem',
              }}
            >
              {uploadingLabel}
            </div>
          )}
          <button
            type="button"
            onClick={handleRemove}
            style={{
              position: 'absolute',
              top: '8px',
              right: '8px',
              width: '26px',
              height: '26px',
              borderRadius: '50%',
              border: 'none',
              background: 'rgba(0,0,0,0.5)',
              color: '#fff',
              cursor: 'pointer',
              fontSize: '0.9rem',
            }}
            title="移除"
          >
            ×
          </button>
        </div>
      ) : (
        <div
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          style={{
            width: '100%',
            height: '160px',
            borderRadius: '12px',
            border: `2px dashed ${dragOver ? 'var(--brand)' : 'var(--border)'}`,
            background: 'var(--surface-2)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            gap: '6px',
            transition: 'border-color 0.2s',
          }}
        >
          <span style={{ fontSize: '2rem' }}>🖼️</span>
          <span className="hint" style={{ fontSize: '0.85rem' }}>
            点击或拖拽图片到此处上传
          </span>
        </div>
      )}
      {error && (
        <p style={{ color: 'oklch(0.5 0.16 22)', fontSize: '0.8rem', marginTop: '6px' }}>
          {error}
        </p>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleChange}
      />
    </div>
  )
}

export default ImageUploader
