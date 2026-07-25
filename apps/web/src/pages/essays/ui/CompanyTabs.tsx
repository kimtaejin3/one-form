import type { KeyboardEvent } from 'react'

/** 전체 문항을 보는 기본 필터. 회사 목록 앞에 끼워 넣어 같은 탭 목록으로 다룬다. */
export const ALL_COMPANIES = '전체'

/**
 * 회사 필터 탭. WAI-ARIA tabs 패턴 — 선택된 탭만 tabIndex 0(roving tabindex)이라
 * Tab 한 번으로 들어와 ←/→로 회사를 옮긴다.
 */
export default function CompanyTabs({
  companies,
  selected,
  onSelect,
}: {
  companies: string[]
  selected: string
  onSelect: (company: string) => void
}) {
  function move(e: KeyboardEvent<HTMLDivElement>) {
    const dir = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0
    if (!dir) return
    e.preventDefault()
    const next = (companies.indexOf(selected) + dir + companies.length) % companies.length
    onSelect(companies[next])
    e.currentTarget.querySelectorAll<HTMLButtonElement>('[role="tab"]')[next]?.focus()
  }

  return (
    <div className="job-filters" role="tablist" aria-label="회사 필터" onKeyDown={move}>
      {companies.map((c) => (
        <button
          key={c}
          type="button"
          role="tab"
          id={c === selected ? 'essay-company-tab' : undefined}
          aria-selected={c === selected}
          aria-controls="essay-company-panel"
          tabIndex={c === selected ? 0 : -1}
          className={`filter-chip${c === selected ? ' filter-chip--on' : ''}`}
          onClick={() => onSelect(c)}
        >
          {c}
        </button>
      ))}
    </div>
  )
}
