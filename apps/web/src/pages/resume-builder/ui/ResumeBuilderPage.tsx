import { useMemo, useState } from 'react'
import { useQuery, useSuspenseQuery } from '@tanstack/react-query'
import { Button } from '@one-form/design-system'
import {
  resumeSeedQuery,
  resumeTemplatesQuery,
  type ResumeMaterial,
  type ResumeState,
} from '@/entities/resume'
import { MaterialsPanel } from '@/features/resume-materials'
import { ChatBubble } from '@/features/resume-chat'

// kind='resume'는 이력서 빌더, 'portfolio'는 포트폴리오 빌더 — 같은 UI를 기본 템플릿만 달리해 재사용.
export function ResumeBuilderPage({ kind = 'resume' }: { kind?: string }) {
  const { data: seed } = useSuspenseQuery(resumeSeedQuery)
  const { data: templates } = useSuspenseQuery(resumeTemplatesQuery)
  const [state, setState] = useState<ResumeState>(() => {
    const preset = templates.find((t) => t.kind === kind)?.preset
    return preset ? { ...seed, style: preset } : seed
  })
  const [materials, setMaterials] = useState<ResumeMaterial[]>([])

  // state가 바뀔 때마다 미리보기 HTML을 서버에서 재렌더.
  // 일반 useQuery(non-suspense)로 백그라운드에서만 갱신 — 페이지 전체를 다시 suspend시키지 않는다.
  const stateKey = useMemo(() => JSON.stringify(state), [state])
  const { data: html = '' } = useQuery({
    queryKey: ['resume-preview', stateKey],
    queryFn: () =>
      fetch('/api/resume/preview', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ state }),
      }).then((res) => res.text()),
  })

  const download = async () => {
    const res = await fetch('/api/resume/render', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ state }),
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = kind === 'portfolio' ? 'portfolio.pdf' : 'resume.pdf'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="resume-builder">
      <div className="resume-side">
        <MaterialsPanel
          state={state}
          materials={materials}
          kind={kind}
          onAddMaterial={(m) => setMaterials((ms) => [...ms, m])}
          onTemplate={(preset) => setState((s) => ({ ...s, style: preset }))}
        />
        <div className="resume-side-foot">
          <ChatBubble state={state} materials={materials} onState={setState} />
          <Button className="resume-download" onClick={download}>
            📄 PDF 내려받기
          </Button>
        </div>
      </div>
      <div className="resume-preview">
        <iframe title="이력서 미리보기" srcDoc={html} sandbox="" />
      </div>
    </div>
  )
}
