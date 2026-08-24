import { useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { Button } from '@one-form/design-system'
import { Dropzone } from '@/shared/ui'
import { TemplateModal } from './TemplateModal'
import {
  resumeTemplatesQuery,
  type ResumeMaterial,
  type ResumeState,
  type ResumeStyle,
} from '@/entities/resume'
import { useExtractMaterial } from '../model'

interface Props {
  state: ResumeState
  materials: ResumeMaterial[]
  onAddMaterial: (m: ResumeMaterial) => void
  onTemplate: (preset: ResumeStyle) => void
  kind: string // resume | portfolio
}

export function MaterialsPanel({ state, materials, onAddMaterial, onTemplate, kind }: Props) {
  const { data: templates } = useSuspenseQuery(resumeTemplatesQuery)
  const extract = useExtractMaterial(onAddMaterial)
  const [note, setNote] = useState('')
  const [tplOpen, setTplOpen] = useState(false)
  const current = templates.find((t) => t.id === state.style.template)

  return (
    <aside className="resume-materials">
      <section>
        <h3>템플릿</h3>
        <div className="resume-template-current">
          <span className="resume-template-name">{current?.name ?? state.style.template}</span>
          <Button size="sm" variant="ghost" onClick={() => setTplOpen(true)}>
            변경
          </Button>
        </div>
        <TemplateModal
          open={tplOpen}
          onClose={() => setTplOpen(false)}
          state={state}
          onTemplate={onTemplate}
          kind={kind}
        />
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
          className="of-input"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="메모·경험을 붙여넣기"
        />
        <Button
          size="sm"
          disabled={!note.trim()}
          onClick={() => {
            onAddMaterial({ kind: 'note', label: '메모', text: note })
            setNote('')
          }}
        >
          메모 추가
        </Button>
        <ul className="resume-material-chips">
          {materials.map((m, i) => (
            <li key={i}>{m.label || m.kind}</li>
          ))}
        </ul>
      </section>
    </aside>
  )
}
