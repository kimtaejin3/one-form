import { Button, Card, Dropdown } from '@one-form/design-system'
import { slotKey, type AnswerSlot, type Question } from '@/entities/essay'
import { useGenerateDraft } from '@/features/generate-draft'
import { useSaveAnswer } from '@/features/save-answer'

/**
 * (문항 × 기업) 슬롯 하나의 작성 패널. 답변은 회사마다 별개라 어느 기업으로 쓰는지가 늘 붙는다 —
 * 기업별 뷰에선 고정(칩), 문항별 뷰에선 상단 Dropdown(`companies`)으로 고른다.
 * 본문은 페이지가 슬롯 키별로 보관하므로 문항·기업을 옮겼다 돌아와도 쓰던 내용이 남는다.
 */
export default function EssayEditor({
  question,
  slot,
  companies,
  onPickCompany,
  text,
  onChangeText,
}: {
  question: Question
  slot: AnswerSlot
  /** 문항별 뷰에서 고를 수 있는 기업들. 기업별 뷰(고정 맥락)에선 넘기지 않는다. */
  companies?: string[]
  onPickCompany?: (company: string) => void
  text: string
  onChangeText: (key: string, text: string) => void
}) {
  const key = slotKey(question.id, slot.company)
  const gen = useGenerateDraft(onChangeText)
  const save = useSaveAnswer()
  const mine = gen.variables?.key === key // 다른 슬롯의 생성 상태를 여기 표시하지 않는다
  const savingMine =
    save.variables?.questionId === question.id && save.variables.company === slot.company
  const over = question.char_limit == null ? 0 : text.length - question.char_limit
  const done = slot.status === '초안 완료'

  // 작성 중인 본문을 초안이 말없이 덮어쓰지 않게 한 번 확인한다.
  function generate() {
    if (text && !window.confirm('작성 중인 내용을 AI 초안으로 덮어씁니다. 계속할까요?')) return
    gen.mutate({ questionId: question.id, key })
  }

  // 상태는 본문 유무가 정한다 — 빈 답은 "미작성"으로 되돌아가고,
  // 사용자가 표시해 둔 "초안 완료"는 그냥 저장했다고 내려가지 않는다.
  function persist(status: AnswerSlot['status'] = done ? '초안 완료' : '작성 중') {
    save.mutate({
      questionId: question.id,
      company: slot.company,
      content: text,
      status: text ? status : '미작성',
    })
  }

  return (
    <Card className="of-essay-panel">
      <div className="row">
        <span className="of-chip">{question.tag}</span>
        {companies && onPickCompany ? (
          <Dropdown
            label="작성할 기업"
            options={companies.map((c) => ({ value: c, label: c }))}
            value={slot.company}
            onChange={onPickCompany}
          />
        ) : (
          <span className="of-chip">{slot.company}</span>
        )}
        <span className="of-mono">
          {slot.status}
          {slot.deadline && ` · 마감 ${slot.deadline}`}
        </span>
      </div>

      <p className="of-essay-panel__q">{question.prompt}</p>

      <div className="row">
        <Button size="sm" disabled={gen.isPending && mine} onClick={generate}>
          {gen.isPending && mine ? '생성 중…' : text ? 'AI 초안 다시 생성' : 'AI 초안 생성'}
        </Button>
        {gen.isError && mine && <span className="of-essay-warn">초안 생성에 실패했어요.</span>}
      </div>

      <textarea
        className="of-essay-text"
        aria-label="자소서 본문"
        placeholder={`${slot.company}에 낼 답변을 직접 작성하거나, AI 초안으로 시작해보세요.`}
        value={text}
        onChange={(e) => onChangeText(key, e.target.value)}
      />

      <div className={`of-essay-count${over > 0 ? ' of-essay-count--over' : ''}`}>
        {question.char_limit == null
          ? `${text.length}자 · 제한 없음`
          : `${text.length} / ${question.char_limit}자${over > 0 ? ` · ${over}자 초과` : ''}`}
      </div>

      <div className="row of-essay-actions">
        <label className="of-essay-done">
          <input
            type="checkbox"
            checked={done}
            disabled={!text || (save.isPending && savingMine)}
            onChange={(e) => persist(e.target.checked ? '초안 완료' : '작성 중')}
          />
          초안 완료
        </label>
        <Button
          size="sm"
          variant="ghost"
          disabled={save.isPending && savingMine}
          onClick={() => persist()}
        >
          {save.isPending && savingMine ? '저장 중…' : '저장'}
        </Button>
        {save.isError && savingMine && <span className="of-essay-warn">저장에 실패했어요.</span>}
      </div>
    </Card>
  )
}
