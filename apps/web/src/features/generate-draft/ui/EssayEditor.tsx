import { useState } from 'react'
import { Button, Card } from '@one-form/design-system'
import type { Essay } from '@/entities/essay'
import { useGenerateDraft } from '../model'

/**
 * 선택한 문항 하나의 작성 패널. 초안은 textarea 초깃값으로 들어가 이어서 편집할 수 있다.
 * 문항이 바뀌면 페이지가 key로 리마운트해 본문 상태를 리셋한다.
 */
export default function EssayEditor({ essay }: { essay: Essay }) {
  const [text, setText] = useState('')
  const gen = useGenerateDraft(essay.id, setText)
  const over = text.length - essay.char_limit

  // 작성 중인 본문을 초안이 말없이 덮어쓰지 않게 한 번 확인한다.
  function generate() {
    if (text && !window.confirm('작성 중인 내용을 AI 초안으로 덮어씁니다. 계속할까요?')) return
    gen.mutate()
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
        <Button size="sm" disabled={gen.isPending} onClick={generate}>
          {gen.isPending ? '생성 중…' : text ? 'AI 초안 다시 생성' : 'AI 초안 생성'}
        </Button>
        {gen.isError && <span className="of-essay-warn">초안 생성에 실패했어요.</span>}
      </div>

      <textarea
        className="of-essay-text"
        aria-label="자소서 본문"
        placeholder="직접 작성하거나, AI 초안으로 시작해보세요."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <div className={`of-essay-count${over > 0 ? ' of-essay-count--over' : ''}`}>
        {text.length} / {essay.char_limit}자{over > 0 && ` · ${over}자 초과`}
      </div>
    </Card>
  )
}
