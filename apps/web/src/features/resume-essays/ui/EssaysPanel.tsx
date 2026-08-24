import { useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { Button } from '@one-form/design-system'
import {
  resumeEssayQuestionsQuery,
  type ResumeEssay,
  type ResumeState,
} from '@/entities/resume'
import { useEssayDraft } from '../model'

interface Props {
  state: ResumeState
  onDoc: (patch: Partial<ResumeState['doc']>) => void
}

// 공통 질문은행에서 필요한 문항만 골라 자기소개서를 구성한다.
export function EssaysPanel({ state, onDoc }: Props) {
  const { data: questions } = useSuspenseQuery(resumeEssayQuestionsQuery)
  const { essays } = state.doc
  const [note, setNote] = useState('')
  const [selectedId, setSelectedId] = useState('')

  const draft = useEssayDraft((index, text, msg) => {
    if (text) {
      const next = essays.map((e, i) => (i === index ? { ...e, answer: text } : e))
      onDoc({ essays: next })
    }
    setNote(msg)
  })

  const addQuestion = () => {
    const question = questions.find((item) => String(item.id) === selectedId)
    if (!question || essays.some((essay) => essay.question === question.prompt)) return
    onDoc({ essays: [...essays, {
      question: question.prompt,
      answer: '',
      char_limit: question.char_limit ?? null,
    } as ResumeEssay] })
    setSelectedId('')
  }

  const setAnswer = (i: number, answer: string) =>
    onDoc({ essays: essays.map((e, idx) => (idx === i ? { ...e, answer } : e)) })

  const removeAt = (i: number) => onDoc({ essays: essays.filter((_, idx) => idx !== i) })

  return (
    <section className="resume-essays">
      <h3>자기소개서</h3>

      <div className="resume-essays__picker">
        <label className="resume-essays__row">
          <span>문항 선택</span>
          <select
            className="of-input"
            value={selectedId}
            onChange={(event) => setSelectedId(event.target.value)}
          >
            <option value="">문항을 선택하세요</option>
            {questions.map((question) => (
              <option key={question.id} value={question.id}>
                [{question.tag}] {question.prompt}
              </option>
            ))}
          </select>
        </label>
        <Button size="sm" disabled={!selectedId} onClick={addQuestion}>
          문항 추가
        </Button>
      </div>

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
