import { useMemo, useState } from 'react'
import { useQuery, useSuspenseQuery } from '@tanstack/react-query'
import { resumeSeedQuery, type ResumeMaterial, type ResumeState } from '@/entities/resume'
import { MaterialsPanel } from '@/features/resume-materials'
import { ChatPanel } from '@/features/resume-chat'

export function ResumeBuilderPage() {
  const { data: seed } = useSuspenseQuery(resumeSeedQuery)
  const [state, setState] = useState<ResumeState>(() => seed)
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
    a.download = 'resume.pdf'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="resume-builder">
      <MaterialsPanel
        state={state}
        materials={materials}
        onAddMaterial={(m) => setMaterials((ms) => [...ms, m])}
        onTemplate={(templateId) => setState((s) => ({ ...s, style: { ...s.style, template: templateId } }))}
      />
      <div className="resume-preview">
        <iframe title="이력서 미리보기" srcDoc={html} />
        <button className="resume-download" onClick={download}>
          📄 PDF 내려받기
        </button>
      </div>
      <ChatPanel state={state} materials={materials} onState={setState} />
    </div>
  )
}
