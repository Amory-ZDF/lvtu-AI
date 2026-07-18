/**
 * 开始规划页 (page-start)
 * 表单提交后调用异步推荐接口获取 jobId，通过 SSE 监听真实进度
 * 完成后从 job.output_data 取推荐结果存入 tripStore，跳转 /destinations
 */

import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { recommendDestinationsAsync } from '@/services/planning'
import { trackAnalyticsEvent } from '@/services/analytics'
import { useJobProgress } from '@/hooks/useJobProgress'
import { useTripStore, type StartFormDraft } from '@/store/tripStore'
import { useUIStore } from '@/store/uiStore'
import type { DestinationRecommendationRequest, DestinationRecommendationPayload } from '@/types'

interface PrefSlider {
  label: string
  value: number
}

/** 生成步骤文案（基于真实流程） */
const GEN_STEPS = [
  '🔍 分析偏好中...',
  '🌤️ 匹配季节与天气...',
  '📍 检索目的地热点数据...',
  '✨ 生成推荐结果...',
]

function formatDateInput(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function createDefaultFormDraft(): StartFormDraft {
  const today = new Date()
  const endDate = new Date(today)
  endDate.setDate(today.getDate() + 2)
  return {
    interest: '放松的海边，适合拍照的文艺小镇',
    departure: '北京',
    budget: '3000-5000 元',
    startDate: formatDateInput(today),
    endDate: formatDateInput(endDate),
    extra: '',
    prefs: [
      { label: '🌿 自然风光', value: 75 },
      { label: '🍜 美食探索', value: 55 },
      { label: '🏛️ 人文历史', value: 35 },
    ],
  }
}

/** 根据 progress 映射到步骤索引 */
function progressToStep(progress: number): number {
  if (progress >= 76) return 3
  if (progress >= 51) return 2
  if (progress >= 26) return 1
  return 0
}

/** 从 job.output_data 解析推荐结果 */
function parseDestinations(
  data: Record<string, unknown> | null,
): DestinationRecommendationPayload | null {
  if (!data) return null
  const dests = data.destinations
  if (!Array.isArray(dests)) return null
  return {
    query_summary:
      typeof data.query_summary === 'string' ? data.query_summary : '基于你的偏好生成',
    destinations: dests as DestinationRecommendationPayload['destinations'],
  }
}

export function StartPage() {
  const navigate = useNavigate()
  const showToast = useUIStore((s) => s.showToast)
  const setDestinations = useTripStore((s) => s.setDestinations)
  const setLastRecommendRequest = useTripStore((s) => s.setLastRecommendRequest)
  const startFormDraft = useTripStore((s) => s.startFormDraft)
  const setStartFormDraft = useTripStore((s) => s.setStartFormDraft)
  const { progress, status, outputData, error: jobError, start, reset } = useJobProgress()
  const initialDraft = startFormDraft || createDefaultFormDraft()

  const [generating, setGenerating] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [prefs, setPrefs] = useState<PrefSlider[]>(() =>
    initialDraft.prefs.map((pref) => ({ ...pref })),
  )

  // 表单字段
  const [interest, setInterest] = useState(initialDraft.interest)
  const [departure, setDeparture] = useState(initialDraft.departure)
  const [budget, setBudget] = useState(initialDraft.budget)
  const [startDate, setStartDate] = useState(initialDraft.startDate)
  const [endDate, setEndDate] = useState(initialDraft.endDate)
  const [extra, setExtra] = useState(initialDraft.extra)

  const buildDraft = (): StartFormDraft => ({
    interest,
    departure,
    budget,
    startDate,
    endDate,
    extra,
    prefs: prefs.map((pref) => ({ ...pref })),
  })

  /** 解析预算区间为 min/max */
  const parseBudget = (raw: string): { min: number; max: number } => {
    const nums = raw.match(/\d+/g)
    if (nums && nums.length >= 2) {
      return { min: Number(nums[0]), max: Number(nums[1]) }
    }
    return { min: 1000, max: 5000 }
  }

  /** 根据日期计算天数 */
  const calcDuration = (): number => {
    if (!startDate || !endDate) return 3
    const diff = (new Date(endDate).getTime() - new Date(startDate).getTime()) / 86400000
    return Math.max(1, Math.round(diff) + 1)
  }

  /** 根据日期推断季节 */
  const inferSeason = (): string => {
    if (!startDate) return '春'
    const month = new Date(startDate).getMonth() + 1
    if (month >= 3 && month <= 5) return '春'
    if (month >= 6 && month <= 8) return '夏'
    if (month >= 9 && month <= 11) return '秋'
    return '冬'
  }

  /** 构建请求 payload */
  const buildPayload = (): DestinationRecommendationRequest => {
    const { min, max } = parseBudget(budget)
    const interests: string[] = []
    if (interest) interests.push(interest)
    prefs.forEach((p) => {
      if (p.value >= 60) interests.push(p.label)
    })
    if (extra) interests.push(extra)
    return {
      departure_city: departure || null,
      budget_min: min,
      budget_max: max,
      duration_days: calcDuration(),
      season: inferSeason(),
      interests,
    }
  }

  const buildAnalyticsMetadata = (payload: DestinationRecommendationRequest) => ({
    destination_count: undefined as number | undefined,
    duration_days: payload.duration_days,
    budget_min: payload.budget_min ?? undefined,
    budget_max: payload.budget_max ?? undefined,
    budget_label: budget,
    departure_city: payload.departure_city,
    season: payload.season,
    interests: payload.interests,
  })

  useEffect(() => {
    setStartFormDraft(buildDraft())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interest, departure, budget, startDate, endDate, extra, prefs])

  const handleGenerate = async (e: FormEvent) => {
    e.preventDefault()
    setGenerating(true)
    setSubmitError(null)
    reset()

    try {
      const payload = buildPayload()
      setLastRecommendRequest(payload)
      setStartFormDraft(buildDraft())
      const job = await recommendDestinationsAsync(payload)
      // 若任务已同步完成，直接取结果（后端 status 为 "completed"）
      if ((job.status === 'succeeded' || job.status === 'completed') && job.output_data) {
        const parsed = parseDestinations(job.output_data)
        if (parsed) {
          setDestinations(parsed)
          trackAnalyticsEvent({
            event_name: 'destination_recommendation_success',
            event_category: 'conversion',
            metadata: {
              ...buildAnalyticsMetadata(payload),
              destination_count: parsed.destinations.length,
            },
          })
          setGenerating(false)
          navigate('/destinations')
          return
        }
      }
      if (job.status === 'failed') {
        throw new Error(job.error_message || '推荐任务失败')
      }
      // 启动 SSE 监听
      start(job.job_id)
    } catch (err) {
      setGenerating(false)
      const msg = err instanceof Error ? err.message : '推荐失败，请重试'
      setSubmitError(msg)
      showToast(msg)
    }
  }

  // 监听任务状态变化
  useEffect(() => {
    if (status === 'succeeded') {
      const parsed = parseDestinations(outputData)
      if (parsed) {
        const payload = buildPayload()
        setLastRecommendRequest(payload)
        setStartFormDraft(buildDraft())
        setDestinations(parsed)
        trackAnalyticsEvent({
          event_name: 'destination_recommendation_success',
          event_category: 'conversion',
          metadata: {
            ...buildAnalyticsMetadata(payload),
            destination_count: parsed.destinations.length,
          },
        })
        showToast('推荐结果已生成')
        setTimeout(() => {
          setGenerating(false)
          navigate('/destinations')
        }, 500)
      } else {
        setGenerating(false)
        setSubmitError('推荐结果解析失败，请重试')
        showToast('推荐结果解析失败')
      }
    } else if (status === 'failed') {
      setGenerating(false)
      const msg = jobError || '推荐任务失败，请重试'
      setSubmitError(msg)
      showToast(msg)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status])

  const handleRetry = () => {
    setSubmitError(null)
    // 重新提交表单
    handleGenerate({ preventDefault: () => {} } as FormEvent)
  }

  const handlePrefChange = (idx: number, value: number) => {
    setPrefs((prev) => prev.map((p, i) => (i === idx ? { ...p, value } : p)))
  }

  const genStep = progressToStep(progress)
  const failed = status === 'failed'

  return (
    <div className="page">
      <button className="back-link" onClick={() => navigate('/')}>
        ← 返回首页
      </button>
      <h2>告诉我们你的旅行偏好</h2>
      <p className="hint" style={{ marginBottom: '22px' }}>
        AI 会根据你的偏好推荐最匹配的目的地
      </p>

      <div className="steps-bar">
        <div className="step-item">
          <div className="step-circle current">1</div>
          <span className="step-label active">偏好输入</span>
        </div>
        <div className="step-line"></div>
        <div className="step-item">
          <div className="step-circle">2</div>
          <span className="step-label">智能分析</span>
        </div>
        <div className="step-line"></div>
        <div className="step-item">
          <div className="step-circle">3</div>
          <span className="step-label">目的地推荐</span>
        </div>
        <div className="step-line"></div>
        <div className="step-item">
          <div className="step-circle">4</div>
          <span className="step-label">生成方案</span>
        </div>
      </div>

      <div className="start-form-wrap">
        {generating ? (
          <div className="gen-preview" style={{ flex: 1, maxWidth: '100%' }}>
            <div className="gen-card show">
              <div className="spinner"></div>
              <p>
                <strong>正在为你匹配目的地...</strong>
              </p>
              <div className="gen-steps">{GEN_STEPS[genStep]}</div>
              {/* 真实进度条 */}
              <div style={{ width: '100%', maxWidth: '320px', marginTop: '14px' }}>
                <div
                  style={{
                    height: '8px',
                    borderRadius: '4px',
                    background: 'var(--surface-2)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      width: `${progress}%`,
                      background: 'var(--brand)',
                      transition: 'width 0.3s ease',
                      borderRadius: '4px',
                    }}
                  />
                </div>
                <p
                  className="hint"
                  style={{ fontSize: '0.78rem', marginTop: '6px', textAlign: 'center' }}
                >
                  {progress}%
                </p>
              </div>
              {failed && (
                <div style={{ marginTop: '14px' }}>
                  <p
                    style={{
                      color: 'oklch(0.5 0.16 22)',
                      fontSize: '0.85rem',
                      marginBottom: '10px',
                    }}
                  >
                    {jobError || '推荐失败'}
                  </p>
                  <button
                    className="btn btn-primary"
                    style={{ width: '100%', justifyContent: 'center' }}
                    onClick={handleRetry}
                  >
                    重试
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <form className="start-form form-card" onSubmit={handleGenerate}>
            {submitError && (
              <div className="login-error" style={{ marginBottom: '12px' }}>{submitError}</div>
            )}
            <div className="form-group">
              <label>🎯 你想去什么样的地方？</label>
              <input
                type="text"
                placeholder="例如：安静的海边、适合拍照的小城…"
                value={interest}
                onChange={(e) => setInterest(e.target.value)}
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>📍 出发地</label>
                <input
                  type="text"
                  placeholder="城市名称"
                  value={departure}
                  onChange={(e) => setDeparture(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>💰 预算</label>
                <select value={budget} onChange={(e) => setBudget(e.target.value)}>
                  <option>3000-5000 元</option>
                  <option>1000-3000 元</option>
                  <option>5000-8000 元</option>
                  <option>8000+ 元</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>📅 出行日期</label>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  style={{ flex: 1 }}
                />
                <span style={{ color: 'var(--ink-tertiary)', fontSize: '0.85rem' }}>至</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  style={{ flex: 1 }}
                />
              </div>
            </div>
            <div className="form-group">
              <label>🎨 风格偏好</label>
              <div className="pref-sliders">
                {prefs.map((pref, idx) => (
                  <div key={pref.label} className="pref-row">
                    <span className="pref-label">{pref.label}</span>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      value={pref.value}
                      onChange={(e) => handlePrefChange(idx, Number(e.target.value))}
                    />
                    <span className="pref-val">{pref.value}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="form-group">
              <label>💬 其他要求</label>
              <input
                type="text"
                placeholder="例如：适合带娃、需要无障碍设施、宠物友好…"
                value={extra}
                onChange={(e) => setExtra(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>🏃 节奏偏好</label>
              <div className="slider-wrap">
                <input type="range" min={1} max={10} defaultValue={4} />
                <div className="slider-labels">
                  <span>慢节奏 · 深度</span>
                  <span>紧凑 · 多打卡</span>
                </div>
              </div>
            </div>
            <button
              className="btn btn-primary btn-lg"
              type="submit"
              style={{ width: '100%', justifyContent: 'center' }}
            >
              🔮 为我推荐目的地
            </button>
          </form>
        )}
        {!generating && (
          <div className="gen-preview">
            <div className="gen-card" id="genCard">
              <div className="spinner"></div>
              <p>
                <strong>正在为你匹配目的地...</strong>
              </p>
              <div className="gen-steps" id="genSteps">
                🔍 分析偏好中...
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default StartPage
