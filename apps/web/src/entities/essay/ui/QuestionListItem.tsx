import { fillCompany, type Question } from '../model'

const STATUS_MOD: Record<string, string> = {
  미작성: 'todo',
  '작성 중': 'doing',
  '초안 완료': 'done',
}

/**
 * 문항 목록의 한 줄. 답변은 문항에 붙어 재사용되므로 회사가 아니라 유형·상태를 앞세우고,
 * 이 문항을 쓰는 기업 수(없으면 공통)를 붙여 재사용 범위를 보여준다.
 * 기업 맥락(`company`)이 있으면 질문·미리보기를 그 회사명으로 치환해 읽힌다.
 */
export default function QuestionListItem({
  question,
  company,
  selected,
  onSelect,
}: {
  question: Question
  company?: string
  selected: boolean
  onSelect: () => void
}) {
  const used = question.companies.length

  return (
    <button
      type="button"
      className={`of-essay-item${selected ? ' of-essay-item--on' : ''}`}
      aria-current={selected ? 'true' : undefined}
      onClick={onSelect}
    >
      <span className="of-essay-item__meta">
        <span className="of-essay-item__who">{question.tag}</span>
        <span className={`of-status of-status--${STATUS_MOD[question.status] ?? 'todo'}`}>
          {question.status}
        </span>
      </span>
      <span className="of-essay-item__q">{fillCompany(question.prompt, company)}</span>
      <span className="of-essay-item__preview">
        {fillCompany(question.answer, company).split('\n')[0].trim() || '미작성'}
      </span>
      <span className="of-essay-item__meta of-mono">
        {used ? `${used}개 기업 사용` : '공통'} · {question.char_limit}자
      </span>
    </button>
  )
}
