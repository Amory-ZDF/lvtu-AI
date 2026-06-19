import { modalRegistry } from '../data/baseline'
import { useDemoState } from '../hooks/useDemoState'

export function ModalHost() {
  const { activeModal, closeModal, setStatus, variant } = useDemoState()
  if (!activeModal || !modalRegistry[activeModal]) return null
  const modal = modalRegistry[activeModal]

  const commit = () => {
    if (['tripBrief', 'destinationCompare'].includes(activeModal))
      setStatus('generation', 'success')
    if (activeModal === 'importConfirm') setStatus('import', 'success')
    if (['auth', 'planConfirm'].includes(activeModal))
      setStatus('save', 'success')
    if (['publishCommunity', 'shareCommunity'].includes(activeModal))
      setStatus('publish', 'success')
    if (activeModal === 'deleteConfirm') setStatus('delete', 'success')
    closeModal()
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <div aria-modal="true" className="modal-card" role="dialog">
        <div className="modal-head">
          <div>
            <p className="eyebrow">{variant.tone}</p>
            <h2>{modal.title}</h2>
          </div>
          <button className="icon-button" onClick={closeModal} type="button">
            关闭
          </button>
        </div>
        <p className="modal-body">{modal.body}</p>
        <ul className="plain-list">
          {modal.highlights.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <div className="modal-actions">
          <button className="ghost-button" onClick={closeModal} type="button">
            取消
          </button>
          <button className="primary-button" onClick={commit} type="button">
            标记为已演示
          </button>
        </div>
      </div>
    </div>
  )
}
