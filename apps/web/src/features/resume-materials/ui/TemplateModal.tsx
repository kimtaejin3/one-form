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

// 템플릿 미리보기는 '샘플' 데이터로 렌더한다 — 내 실제 이력서가 아니라 템플릿 스타일을 고르는 화면이므로.
const SAMPLE_DOC = {
  header: {
    name: '홍길동',
    contact: ['hong@example.com', '010-1234-5678', '서울특별시'],
    links: [{ label: 'GitHub', url: '#' }],
  },
  summary: '사용자 경험을 고민하는 개발자입니다. 구조와 도구로 팀 생산성을 높여왔습니다.',
  sections: [
    {
      id: 'career', type: 'career', title: '경력', order: 0, visible: true,
      items: [
        {
          title: '프론트엔드 개발', org: '샘플컴퍼니', period: '2022.01 ~ 현재',
          bullets: ['핵심 서비스 화면 개발 및 운영', '렌더링 최적화로 로딩 30% 단축'],
          stack: ['React', 'TypeScript'],
        },
      ],
    },
    {
      id: 'project', type: 'project', title: '프로젝트', order: 1, visible: true,
      items: [
        {
          title: '디자인 시스템 구축', org: '사내', period: '2023',
          note: '공통 컴포넌트 라이브러리 설계로 신규 화면을 조합만으로 개발',
          bullets: ['재사용 컴포넌트 40여 개 정의'], stack: ['Storybook'],
        },
      ],
    },
    {
      id: 'skill', type: 'skill', title: '스킬', order: 2, visible: true,
      items: [{ stack: ['React', 'TypeScript', 'Next.js', 'Node.js', 'CSS'] }],
    },
  ],
}

// 각 템플릿을 샘플 데이터로 렌더해 A4 축소 미리보기로 보여준다.
function TemplateCard({
  template,
  active,
  onSelect,
}: {
  template: ResumeTemplate
  active: boolean
  onSelect: (p: ResumeStyle) => void
}) {
  const { data: html = '' } = useQuery({
    queryKey: ['resume-tpl-sample', template.id],
    queryFn: () =>
      fetch('/api/resume/preview', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ state: { doc: SAMPLE_DOC, style: template.preset } }),
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
