import { useEffect, type ReactNode } from 'react'

export type ModalProps = {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
}

/**
 * 오버레이 다이얼로그. 백드롭 클릭·Esc로 닫고, 패널 클릭은 전파를 막는다.
 * role="dialog" aria-modal — 열렸을 때만 렌더한다.
 */
export function Modal({ open, onClose, title, children }: ModalProps) {
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="of-modal" role="presentation" onClick={onClose}>
      <div
        className="of-modal__panel"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <div className="of-modal__head">
            <strong>{title}</strong>
            <button type="button" className="of-modal__close" aria-label="닫기" onClick={onClose}>
              ✕
            </button>
          </div>
        )}
        <div className="of-modal__body">{children}</div>
      </div>
    </div>
  )
}
