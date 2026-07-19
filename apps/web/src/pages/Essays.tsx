import { useState } from 'react'
import { Button, Card } from '@one-form/design-system'
import { post } from '../api'
import { useApi } from '../useApi'

type Essay = {
  id: number
  company: string
  question: string
  char_limit: number
  deadline: string
  status: string
}

export default function Essays() {
  const essays = useApi<Essay[]>('/essays')
  const [drafts, setDrafts] = useState<Record<number, string>>({})
  const [busyId, setBusyId] = useState<number | null>(null)

  async function onDraft(id: number) {
    setBusyId(id)
    const res = await post<{ draft: string }>('/essays/draft', { essay_id: id })
    setDrafts((prev) => ({ ...prev, [id]: res.draft }))
    setBusyId(null)
  }

  return (
    <>
      <h2 className="of-h2">자소서 허브</h2>
      <p className="page-desc">기업별 문항을 글자 수·마감과 함께 관리하고 AI 초안을 생성합니다.</p>
      {!essays ? (
        <p className="of-mono">불러오는 중…</p>
      ) : (
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
                    <Button size="sm" disabled={busyId !== null} onClick={() => onDraft(essay.id)}>
                      {busyId === essay.id ? '생성 중…' : 'AI 초안 생성'}
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </>
  )
}
