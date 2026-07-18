interface AdjustmentProgressDialogProps {
  open: boolean
  progress: number
  instruction: string
}

const STAGES = ['理解修改需求', '生成调整方案', '更新并校验行程']

export function AdjustmentProgressDialog({
  open,
  progress,
  instruction,
}: AdjustmentProgressDialogProps) {
  if (!open) return null

  const activeStage = progress >= 100 ? 2 : progress >= 68 ? 2 : progress >= 34 ? 1 : 0
  const stageText = progress >= 100 ? '行程修改完成，正在刷新页面' : STAGES[activeStage]

  return (
    <div className="adjustment-progress-overlay" role="dialog" aria-modal="true" aria-labelledby="adjustment-progress-title">
      <div className="adjustment-progress-dialog">
        <div className="adjustment-progress-mark" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <h2 id="adjustment-progress-title">正在修改行程</h2>
        <p className="adjustment-progress-stage">{stageText}</p>
        <p className="adjustment-progress-instruction">“{instruction}”</p>

        <div
          className="adjustment-progress-track"
          role="progressbar"
          aria-label="AI 修改行程进度"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress}
        >
          <div className="adjustment-progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <div className="adjustment-progress-meta">
          <span>{STAGES[activeStage]}</span>
          <strong>{progress}%</strong>
        </div>

        <ol className="adjustment-progress-steps">
          {STAGES.map((stage, index) => (
            <li key={stage} className={index < activeStage ? 'done' : index === activeStage ? 'active' : ''}>
              <span aria-hidden="true">{index < activeStage ? '✓' : index + 1}</span>
              {stage}
            </li>
          ))}
        </ol>
        <small>AI 正在分析完整路线，请保持页面开启</small>
      </div>
    </div>
  )
}

export default AdjustmentProgressDialog
