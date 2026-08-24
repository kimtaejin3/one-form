import { useMemo, useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { useQuery, useSuspenseQuery } from '@tanstack/react-query'
import { Button } from '@one-form/design-system'
import {
  resumeSeedQuery,
  resumeTemplatesQuery,
  getSavedDoc,
  upsertSavedDoc,
  newDocId,
  type ResumeMaterial,
  type ResumeState,
} from '@/entities/resume'
import { MaterialsPanel } from '@/features/resume-materials'
import { EssaysPanel } from '@/features/resume-essays'
import { ChatBubble } from '@/features/resume-chat'

// 하나의 빌더가 이력서·포트폴리오를 모두 다룬다. 라우트로 구분:
//   /resume/new?kind=resume|portfolio → 새로, /resume/edit/:id → 저장된 문서 편집.
export function ResumeBuilderPage() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { data: seed } = useSuspenseQuery(resumeSeedQuery)
  const { data: templates } = useSuspenseQuery(resumeTemplatesQuery)

  const existing = id ? getSavedDoc(id) : undefined
  const kind = existing?.kind ?? searchParams.get('kind') ?? 'resume'

  const [docId] = useState(() => existing?.id ?? newDocId())
  const [title, setTitle] = useState(() => existing?.title ?? '')
  const [state, setState] = useState<ResumeState>(() => {
    if (existing) return existing.state
    const preset = templates.find((t) => t.kind === kind)?.preset
    return preset ? { ...seed, style: preset } : seed
  })
  const [materials, setMaterials] = useState<ResumeMaterial[]>([])

  // state가 바뀔 때마다 미리보기 HTML을 서버에서 재렌더(백그라운드 useQuery).
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

  const save = () => {
    const name =
      title.trim() || state.doc.header.name || (kind === 'portfolio' ? '포트폴리오' : '이력서')
    upsertSavedDoc({
      id: docId,
      title: name,
      kind,
      template: state.style.template,
      state,
      updatedAt: Date.now(),
    })
    navigate('/resume')
  }

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
        <div className="resume-materials">
          <EssaysPanel
            state={state}
            onDoc={(patch) => setState((s) => ({ ...s, doc: { ...s.doc, ...patch } }))}
          />
        </div>
        <div className="resume-side-foot">
          <div className="resume-save">
            <input
              className="of-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="문서 이름 (예: 프론트 지원용)"
            />
            <Button onClick={save}>저장</Button>
          </div>
          <ChatBubble state={state} materials={materials} onState={setState} />
          <Button className="resume-download" variant="ghost" onClick={download}>
            📄 PDF 내려받기
          </Button>
        </div>
      </div>
      <div className="resume-preview">
        <iframe title="미리보기" srcDoc={html} sandbox="" />
      </div>
    </div>
  )
}
