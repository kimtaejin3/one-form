import { COMMON, type AnswerSlot, type Question } from '../model'

const STATUS_MOD: Record<string, string> = {
  미작성: 'todo',
  '작성 중': 'doing',
  '초안 완료': 'done',
}

/**
 * 문항 목록의 한 줄. 기업별 뷰는 그 회사 슬롯 하나(`slot`)를 상태·미리보기로 보여주고,
 * 문항별 뷰는 슬롯이 여럿이라 "몇 개 기업에서 썼는지"로 집계해 보여준다.
 */
export default function QuestionListItem({
  question,
  slot,
  selected,
  onSelect,
}: {
  question: Question
  slot?: AnswerSlot
  selected: boolean
  onSelect: () => void
}) {
  const common = question.slots[0]?.company === COMMON
  const written = question.slots.filter((s) => s.status !== '미작성').length
  const shown = slot ?? (common ? question.slots[0] : undefined)
  const badge = shown ? shown.status : `${written}/${question.slots.length} 기업 작성`
  const mod = shown
    ? STATUS_MOD[shown.status]
    : written === 0
      ? 'todo'
      : written === question.slots.length
        ? 'done'
        : 'doing'

  return (
    <button
      type="button"
      className={`of-essay-item${selected ? ' of-essay-item--on' : ''}`}
      aria-current={selected ? 'true' : undefined}
      onClick={onSelect}
    >
      <span className="of-essay-item__meta">
        <span className="of-essay-item__who">{question.tag}</span>
        <span className={`of-status of-status--${mod ?? 'todo'}`}>{badge}</span>
      </span>
      <span className="of-essay-item__q">{question.prompt}</span>
      {/* 슬롯이 하나로 정해진 줄에서만 답변 미리보기가 뜻이 있다(문항별 다기업 행은 집계로 충분). */}
      {shown && (
        <span className="of-essay-item__preview">
          {shown.content.split('\n')[0].trim() || '미작성'}
        </span>
      )}
      {!common && (
        <span className="of-essay-item__companies" aria-label="연결된 기업">
          {question.slots.map((item) => (
            <span key={item.company} className="of-essay-company-chip">
              {item.company}
            </span>
          ))}
        </span>
      )}
      <span className="of-essay-item__meta of-mono">
        {common ? COMMON : `${question.slots.length}개 기업`} · {question.char_limit}자
      </span>
    </button>
  )
}
