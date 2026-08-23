import { useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { Dropzone } from '@/shared/ui'
import { resumeTemplatesQuery, type ResumeMaterial, type ResumeState } from '@/entities/resume'
import { useExtractMaterial } from '../model'

interface Props {
  state: ResumeState
  materials: ResumeMaterial[]
  onAddMaterial: (m: ResumeMaterial) => void
  onTemplate: (templateId: string) => void
}

export function MaterialsPanel({ state, materials, onAddMaterial, onTemplate }: Props) {
  const { data: templates } = useSuspenseQuery(resumeTemplatesQuery)
  const extract = useExtractMaterial(onAddMaterial)
  const [note, setNote] = useState('')

  return (
    <aside className="resume-materials">
      <section>
        <h3>템플릿</h3>
        <div className="resume-template-list">
          {templates.map((t) => (
            <button
              key={t.id}
              className={state.style.template === t.id ? 'active' : ''}
              onClick={() => onTemplate(t.id)}
            >
              {t.name}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h3>자료 추가</h3>
        <Dropzone
          title="이력서 자료를 올려보세요"
          desc="PDF · TXT · MD 지원 — 텍스트를 추출해 AI 편집에 씁니다."
          accept=".pdf,.txt,.md"
          buttonLabel="파일 선택"
          busy={extract.isPending}
          busyLabel="추출 중…"
          onFile={(e) => {
            const f = e.target.files?.[0]
            if (f) extract.mutate(f)
          }}
        />
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="메모·경험을 붙여넣기"
        />
        <button
          disabled={!note.trim()}
          onClick={() => {
            onAddMaterial({ kind: 'note', label: '메모', text: note })
            setNote('')
          }}
        >
          메모 추가
        </button>
        <ul className="resume-material-chips">
          {materials.map((m, i) => (
            <li key={i}>{m.label || m.kind}</li>
          ))}
        </ul>
      </section>
    </aside>
  )
}
