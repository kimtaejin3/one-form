import { useEffect, useRef, useState, type KeyboardEvent } from 'react'

export type DropdownOption = { value: string; label: string }

export type DropdownProps = {
  options: DropdownOption[]
  value: string
  onChange: (value: string) => void
  /** 스크린리더용 이름 (트리거·리스트 aria-label) */
  label?: string
  className?: string
}

/**
 * 커스텀 셀렉트 — 네이티브 <select>가 아니라 버튼 + 스타일된 목록.
 * WAI-ARIA select-only combobox 패턴: 트리거 role="combobox", 목록 role="listbox".
 * 바깥 클릭·Esc로 닫고 ↑/↓로 이동, Enter/Space로 선택한다.
 */
export function Dropdown({ options, value, onChange, label, className }: DropdownProps) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const rootRef = useRef<HTMLDivElement>(null)
  const current = options.find((o) => o.value === value) ?? options[0]

  useEffect(() => {
    if (!open) return
    function onDocDown(e: MouseEvent) {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDocDown)
    return () => document.removeEventListener('mousedown', onDocDown)
  }, [open])

  function openList() {
    setActive(Math.max(0, options.findIndex((o) => o.value === value)))
    setOpen(true)
  }
  function choose(v: string) {
    onChange(v)
    setOpen(false)
  }
  function onKeyDown(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === 'Escape') return setOpen(false)
    if (!open) {
      if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        openList()
      }
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive((i) => (i + 1) % options.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((i) => (i - 1 + options.length) % options.length)
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      choose(options[active].value)
    }
  }

  return (
    <div
      className={['of-dropdown', className].filter(Boolean).join(' ')}
      ref={rootRef}
      onKeyDown={onKeyDown}
    >
      <button
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={label}
        className="of-dropdown__trigger"
        onClick={() => (open ? setOpen(false) : openList())}
      >
        <span className="of-dropdown__value">{current?.label}</span>
        <span className="of-dropdown__caret" aria-hidden>
          ▾
        </span>
      </button>
      {open && (
        <ul className="of-dropdown__list" role="listbox" aria-label={label}>
          {options.map((o, i) => (
            <li
              key={o.value}
              role="option"
              aria-selected={o.value === value}
              className={[
                'of-dropdown__opt',
                i === active && 'of-dropdown__opt--active',
                o.value === value && 'of-dropdown__opt--on',
              ]
                .filter(Boolean)
                .join(' ')}
              onMouseEnter={() => setActive(i)}
              onClick={() => choose(o.value)}
            >
              {o.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
