import { Button, Card } from '@one-form/design-system'
import type { Essay } from '@/entities/essay'
import { useGenerateDraft } from '@/features/generate-draft'
import { useSaveAnswer } from '@/features/save-answer'

/**
 * 선택한 문항 하나의 작성 패널. 본문은 페이지가 문항별로 보관하므로(제어 컴포넌트)
 * 문항을 옮겼다 돌아와도 쓰던 내용이 남고, 저장된 답변은 페이지가 초깃값으로 넣어준다.
 * 초안 생성과 저장이 한 자리에서 일어나 두 mutation을 여기서 함께 배선한다.
 */
export default function EssayEditor({
  essay,
  text,
  onChangeText,
}: {
  essay: Essay
  text: string
  onChangeText: (essayId: number, text: string) => void
}) {
  const gen = useGenerateDraft(onChangeText)
  const save = useSaveAnswer()
  const mine = gen.variables === essay.id // 다른 문항의 생성 상태를 여기 표시하지 않는다
  const savingMine = save.variables?.essayId === essay.id
  const over = text.length - essay.char_limit
  const done = essay.status === '초안 완료'

  // 작성 중인 본문을 초안이 말없이 덮어쓰지 않게 한 번 확인한다.
  function generate() {
    if (text && !window.confirm('작성 중인 내용을 AI 초안으로 덮어씁니다. 계속할까요?')) return
    gen.mutate(essay.id)
  }

  // 상태는 본문 유무가 정한다 — 빈 답은 "미작성"으로 되돌아가고,
  // 사용자가 표시해 둔 "초안 완료"는 그냥 저장했다고 내려가지 않는다.
  function persist(status: Essay['status'] = done ? '초안 완료' : '작성 중') {
    save.mutate({ essayId: essay.id, content: text, status: text ? status : '미작성' })
  }

  return (
    <Card className="of-essay-panel">
      <div className="row">
        <span className="of-chip">{essay.company}</span>
        <span className="of-chip">{essay.tag}</span>
        <span className="of-mono">
          ~{essay.deadline} · {essay.status}
        </span>
      </div>

      <p className="of-essay-panel__q">{essay.question}</p>

      <div className="row">
        <Button size="sm" disabled={gen.isPending && mine} onClick={generate}>
          {gen.isPending && mine ? '생성 중…' : text ? 'AI 초안 다시 생성' : 'AI 초안 생성'}
        </Button>
        {gen.isError && mine && <span className="of-essay-warn">초안 생성에 실패했어요.</span>}
      </div>

      <textarea
        className="of-essay-text"
        aria-label="자소서 본문"
        placeholder="직접 작성하거나, AI 초안으로 시작해보세요."
        value={text}
        onChange={(e) => onChangeText(essay.id, e.target.value)}
      />

      <div className={`of-essay-count${over > 0 ? ' of-essay-count--over' : ''}`}>
        {text.length} / {essay.char_limit}자{over > 0 && ` · ${over}자 초과`}
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
