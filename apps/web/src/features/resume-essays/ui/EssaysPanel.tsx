import { useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { Button } from '@one-form/design-system'
import {
  resumeEssaySetsQuery,
  type ResumeEssay,
  type ResumeState,
} from '@/entities/resume'
import { useEssayDraft } from '../model'

interface Props {
  state: ResumeState
  onDoc: (patch: Partial<ResumeState['doc']>) => void
}

// 자소서 = 특정 기업에 대한 세트. 기업 세트를 고르면 그 기업 문항이 구성되고,
// 문항별로 답변을 쓰거나 AI 초안(기업 분석 반영)을 받는다. PDF 포함 여부도 여기서.
export function EssaysPanel({ state, onDoc }: Props) {
  const { data: sets } = useSuspenseQuery(resumeEssaySetsQuery)
  const { company, essays, include_essays: include } = state.doc
  const [note, setNote] = useState('')

  const draft = useEssayDraft((index, text, msg) => {
    if (text) {
      const next = essays.map((e, i) => (i === index ? { ...e, answer: text } : e))
      onDoc({ essays: next })
    }
    setNote(msg)
  })

  const pickSet = (name: string) => {
    const set = sets.find((s) => s.company === name)
    if (!set) return onDoc({ company: '', essays: [] })
    onDoc({
      company: set.company,
      essays: set.questions.map((q) => ({
        question: q.prompt,
        answer: '',
        char_limit: q.char_limit ?? null,
      })) as ResumeEssay[],
    })
  }

  const setAnswer = (i: number, answer: string) =>
    onDoc({ essays: essays.map((e, idx) => (idx === i ? { ...e, answer } : e)) })

  const removeAt = (i: number) => onDoc({ essays: essays.filter((_, idx) => idx !== i) })

  return (
    <section className="resume-essays">
      <h3>자기소개서</h3>

      <label className="resume-essays__row">
        <span>지원 기업</span>
        <select className="of-input" value={company} onChange={(e) => pickSet(e.target.value)}>
          <option value="">선택 안 함</option>
          {sets.map((s) => (
            <option key={s.company} value={s.company}>
              {s.company} ({s.questions.length}문항)
            </option>
          ))}
        </select>
      </label>

      <label className="resume-essays__toggle">
        <input
          type="checkbox"
          checked={include}
          onChange={(e) => onDoc({ include_essays: e.target.checked })}
        />
        PDF에 자소서 포함
      </label>

      {note && <p className="resume-essays__note">{note}</p>}

      {essays.map((e, i) => (
        <div key={i} className="resume-essay-item">
          <div className="resume-essay-item__q">
            <span>{e.question}</span>
            <button onClick={() => removeAt(i)} title="문항 삭제">
              ✕
            </button>
          </div>
          <textarea
            className="of-input"
            value={e.answer}
            onChange={(ev) => setAnswer(i, ev.target.value)}
            placeholder={e.char_limit ? `${e.char_limit}자 이내` : '답변을 작성하세요'}
          />
          <div className="resume-essay-item__foot">
            <span>
              {e.answer.length}
              {e.char_limit ? ` / ${e.char_limit}자` : '자'}
            </span>
            <Button
              size="sm"
              variant="ghost"
              disabled={draft.isPending}
              onClick={() =>
                draft.mutate({
                  index: i,
                  company,
                  question: e.question,
                  char_limit: e.char_limit ?? null,
                  state,
                })
              }
            >
              {draft.isPending ? '작성 중…' : '✨ AI 초안'}
            </Button>
          </div>
        </div>
      ))}
    </section>
  )
}
