import { Button, Card } from '@one-form/design-system'
import type { Essay } from '@/entities/essay'
import { useGenerateDraft } from '../model'

/**
 * 선택한 문항 하나의 작성 패널. 본문은 페이지가 문항별로 보관하므로(제어 컴포넌트)
 * 문항을 옮겼다 돌아와도 쓰던 내용이 남는다. 초안도 같은 자리에 들어가 이어서 편집할 수 있다.
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
  const mine = gen.variables === essay.id // 다른 문항의 생성 상태를 여기 표시하지 않는다
  const over = text.length - essay.char_limit

  // 작성 중인 본문을 초안이 말없이 덮어쓰지 않게 한 번 확인한다.
  function generate() {
    if (text && !window.confirm('작성 중인 내용을 AI 초안으로 덮어씁니다. 계속할까요?')) return
    gen.mutate(essay.id)
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
    </Card>
  )
}
