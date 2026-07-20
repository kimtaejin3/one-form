import { useState } from 'react'
import { useSuspenseQuery, useMutation } from '@tanstack/react-query'
import { Button, Card } from '@one-form/design-system'
import { post } from '../api'
import { essaysQuery } from '../queries/essays'

type Draft = { essay_id: number; draft: string }

export default function Essays() {
  const { data: essays } = useSuspenseQuery(essaysQuery)
  const [drafts, setDrafts] = useState<Record<number, string>>({})
  const draft = useMutation({
    mutationFn: (id: number) => post<Draft>('/essays/draft', { essay_id: id }),
    onSuccess: (res) => setDrafts((prev) => ({ ...prev, [res.essay_id]: res.draft })),
  })
  const busyId = draft.isPending ? draft.variables : null

  return (
    <div className="stack">
      {essays.map((essay) => (
        <Card key={essay.id}>
          <div className="stack">
            <div className="row">
              <span className="of-chip">{essay.company}</span>
              <span className="of-mono">
                {essay.char_limit}자 · ~{essay.deadline} · {essay.status}
              </span>
            </div>
            <strong>{essay.question}</strong>
            {drafts[essay.id] ? (
              <p className="draft-box">{drafts[essay.id]}</p>
            ) : (
              <div className="row">
                <Button size="sm" disabled={busyId !== null} onClick={() => draft.mutate(essay.id)}>
                  {busyId === essay.id ? '생성 중…' : 'AI 초안 생성'}
                </Button>
              </div>
            )}
          </div>
        </Card>
      ))}
    </div>
  )
}
