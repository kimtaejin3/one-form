import type { Essay } from '../model'

const STATUS_MOD: Record<string, string> = {
  미작성: 'todo',
  '작성 중': 'doing',
  '초안 완료': 'done',
}

/** 회사별 문항 목록의 한 줄. 선택 상태와 진행 상태를 함께 보여준다. */
export default function EssayListItem({
  essay,
  selected,
  onSelect,
}: {
  essay: Essay
  selected: boolean
  onSelect: () => void
}) {
  return (
    <button
      type="button"
      className={`of-essay-item${selected ? ' of-essay-item--on' : ''}`}
      aria-current={selected ? 'true' : undefined}
      onClick={onSelect}
    >
      <span className="of-essay-item__q">{essay.question}</span>
      <span className="of-essay-item__meta">
        <span className={`of-status of-status--${STATUS_MOD[essay.status] ?? 'todo'}`}>
          {essay.status}
        </span>
        <span className="of-mono">
          {essay.tag} · ~{essay.deadline} · {essay.char_limit}자
        </span>
      </span>
    </button>
  )
}
