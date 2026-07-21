import { useState } from 'react'
import { Button, Card } from '@one-form/design-system'
import type { Essay } from '@/entities/essay'
import { useGenerateDraft } from '../model'

/** 자소서 문항 카드 + AI 초안 생성. 초안 상태는 카드마다 격리된다. */
export default function EssayCard({ essay }: { essay: Essay }) {
  const [draft, setDraft] = useState<string | null>(null)
  const gen = useGenerateDraft(essay.id, setDraft)

  return (
    <Card>
      <div className="stack">
        <div className="row">
          <span className="of-chip">{essay.company}</span>
          <span className="of-mono">
            {essay.char_limit}자 · ~{essay.deadline} · {essay.status}
          </span>
        </div>
        <strong>{essay.question}</strong>
        {draft ? (
          <p className="draft-box">{draft}</p>
        ) : (
          <div className="row">
            <Button size="sm" disabled={gen.isPending} onClick={() => gen.mutate()}>
              {gen.isPending ? '생성 중…' : 'AI 초안 생성'}
            </Button>
          </div>
        )}
      </div>
    </Card>
  )
}
