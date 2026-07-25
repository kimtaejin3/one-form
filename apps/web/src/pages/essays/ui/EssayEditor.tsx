import { useRef } from 'react'
import { Button, Card } from '@one-form/design-system'
import { fillCompany, type Question } from '@/entities/essay'
import { useGenerateDraft } from '@/features/generate-draft'
import { useSaveAnswer } from '@/features/save-answer'

const TOKEN = '{회사}'

/**
 * 선택한 문항 하나의 작성 패널. 본문은 **원본(토큰 포함)**을 편집하고 아래 미리보기에
 * 지금 맥락(기업별=그 회사, 문항별=귀사)으로 치환한 결과를 보여준다 — 저장은 원본 그대로.
 * 본문은 페이지가 문항별로 보관하므로 문항을 옮겼다 돌아와도 쓰던 내용이 남는다.
 */
export default function EssayEditor({
  question,
  company,
  text,
  onChangeText,
}: {
  question: Question
  company?: string
  text: string
  onChangeText: (questionId: number, text: string) => void
}) {
  const textRef = useRef<HTMLTextAreaElement>(null)
  const gen = useGenerateDraft(onChangeText)
  const save = useSaveAnswer()
  const mine = gen.variables === question.id // 다른 문항의 생성 상태를 여기 표시하지 않는다
  const savingMine = save.variables?.questionId === question.id
  const over = text.length - question.char_limit
  const done = question.status === '초안 완료'

  // 작성 중인 본문을 초안이 말없이 덮어쓰지 않게 한 번 확인한다.
  function generate() {
    if (text && !window.confirm('작성 중인 내용을 AI 초안으로 덮어씁니다. 계속할까요?')) return
    gen.mutate(question.id)
  }

  // 커서 자리에 토큰을 끼워 넣고, 값이 반영된 다음 프레임에 커서를 토큰 뒤로 옮긴다.
  function insertToken() {
    const el = textRef.current
    const from = el?.selectionStart ?? text.length
    const to = el?.selectionEnd ?? from
    onChangeText(question.id, text.slice(0, from) + TOKEN + text.slice(to))
    requestAnimationFrame(() => {
      el?.focus()
      el?.setSelectionRange(from + TOKEN.length, from + TOKEN.length)
    })
  }

  // 상태는 본문 유무가 정한다 — 빈 답은 "미작성"으로 되돌아가고,
  // 사용자가 표시해 둔 "초안 완료"는 그냥 저장했다고 내려가지 않는다.
  function persist(status: Question['status'] = done ? '초안 완료' : '작성 중') {
    save.mutate({ questionId: question.id, content: text, status: text ? status : '미작성' })
  }

  return (
    <Card className="of-essay-panel">
      <div className="row">
        <span className="of-chip">{question.tag}</span>
        {company && <span className="of-chip">{company}</span>}
        <span className="of-mono">
          {question.status} ·{' '}
          {question.companies.length ? `${question.companies.length}개 기업 사용` : '공통'}
        </span>
      </div>

      <p className="of-essay-panel__q">{fillCompany(question.prompt, company)}</p>

      <div className="row">
        <Button size="sm" disabled={gen.isPending && mine} onClick={generate}>
          {gen.isPending && mine ? '생성 중…' : text ? 'AI 초안 다시 생성' : 'AI 초안 생성'}
        </Button>
        <Button size="sm" variant="ghost" onClick={insertToken}>
          {TOKEN} 삽입
        </Button>
        {gen.isError && mine && <span className="of-essay-warn">초안 생성에 실패했어요.</span>}
      </div>

      <textarea
        ref={textRef}
        className="of-essay-text"
        aria-label="자소서 본문"
        placeholder={`직접 작성하거나, AI 초안으로 시작해보세요. ${TOKEN}는 기업 맥락에 맞춰 치환됩니다.`}
        value={text}
        onChange={(e) => onChangeText(question.id, e.target.value)}
      />

      <div className={`of-essay-count${over > 0 ? ' of-essay-count--over' : ''}`}>
        {text.length} / {question.char_limit}자{over > 0 && ` · ${over}자 초과`}
      </div>

      <div className="of-essay-preview">
        <span className="of-essay-preview__label of-mono">
          미리보기 · {company ?? '기업 맥락 없음'}
        </span>
        <p className="of-essay-preview__body" aria-label="답변 미리보기">
          {fillCompany(text, company) || '아직 작성한 내용이 없어요.'}
        </p>
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
