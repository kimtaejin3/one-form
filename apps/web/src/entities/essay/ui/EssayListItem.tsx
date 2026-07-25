import type { Essay } from '../model'

const STATUS_MOD: Record<string, string> = {
  미작성: 'todo',
  '작성 중': 'doing',
  '초안 완료': 'done',
}

/**
 * 문항 목록의 한 줄. 전체 리스트에서도 어느 회사 문항인지 바로 읽히도록
 * `회사 · 문항유형`을 앞세우고, 저장된 답변 첫 줄을 미리보기로 붙인다.
 */
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
      <span className="of-essay-item__meta">
        <span className="of-essay-item__who">
          {essay.company} · {essay.tag}
        </span>
        <span className={`of-status of-status--${STATUS_MOD[essay.status] ?? 'todo'}`}>
          {essay.status}
        </span>
      </span>
      <span className="of-essay-item__q">{essay.question}</span>
      <span className="of-essay-item__preview">
        {essay.answer.split('\n')[0].trim() || '미작성'}
      </span>
      <span className="of-essay-item__meta of-mono">
        ~{essay.deadline} · {essay.char_limit}자
      </span>
    </button>
  )
}
