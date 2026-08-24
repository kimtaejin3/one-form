import { useSuspenseQuery, useQuery } from '@tanstack/react-query'
import { Button, Modal } from '@one-form/design-system'
import {
  resumeTemplatesQuery,
  type ResumeState,
  type ResumeStyle,
  type ResumeTemplate,
} from '@/entities/resume'

interface Props {
  open: boolean
  onClose: () => void
  state: ResumeState
  onTemplate: (preset: ResumeStyle) => void
  kind: string // resume | portfolio — 이 종류의 템플릿만 보여준다
}

// 각 템플릿을 현재 이력서 내용으로 실제 렌더해 A4 축소 미리보기로 보여준다.
function TemplateCard({
  state,
  template,
  active,
  onSelect,
}: {
  state: ResumeState
  template: ResumeTemplate
  active: boolean
  onSelect: (p: ResumeStyle) => void
}) {
  const { data: html = '' } = useQuery({
    queryKey: ['resume-tpl-preview', template.id, JSON.stringify(state.doc)],
    queryFn: () =>
      fetch('/api/resume/preview', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ state: { ...state, style: template.preset } }),
      }).then((r) => r.text()),
  })
  return (
    <div className={`resume-tpl-card${active ? ' active' : ''}`}>
      <div className="resume-tpl-frame">
        <iframe title={template.name} srcDoc={html} sandbox="" />
      </div>
      <div className="resume-tpl-foot">
        <span>{template.name}</span>
        <Button
          size="sm"
          variant={active ? 'ghost' : 'solid'}
          onClick={() => onSelect(template.preset)}
        >
          {active ? '선택됨' : '선택'}
        </Button>
      </div>
    </div>
  )
}

export function TemplateModal({ open, onClose, state, onTemplate, kind }: Props) {
  const { data: templates } = useSuspenseQuery(resumeTemplatesQuery)
  return (
    <Modal open={open} onClose={onClose} title="템플릿 선택">
      <div className="resume-tpl-grid">
        {templates
          .filter((t) => t.kind === kind)
          .map((t) => (
          <TemplateCard
            key={t.id}
            state={state}
            template={t}
            active={state.style.template === t.id}
            onSelect={(preset) => {
              onTemplate(preset)
              onClose()
            }}
          />
        ))}
      </div>
    </Modal>
  )
}
