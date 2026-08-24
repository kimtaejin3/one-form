import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useSuspenseQuery } from '@tanstack/react-query'
import { Button } from '@one-form/design-system'
import {
  getSavedApplication,
  newApplicationId,
  resumeSeedQuery,
  upsertSavedApplication,
  type ResumeApplicationDocuments,
  type ResumeDocumentKind,
  type ResumeMaterial,
  type ResumeState,
} from '@/entities/resume'
import { MaterialsPanel } from '@/features/resume-materials'
import { EssaysPanel } from '@/features/resume-essays'
import { ChatBubble } from '@/features/resume-chat'

const DOCUMENTS: Array<{ kind: ResumeDocumentKind; label: string; filename: string }> = [
  { kind: 'resume', label: '이력서', filename: '이력서' },
  { kind: 'career', label: '경력기술서', filename: '경력기술서' },
  { kind: 'essay', label: '자기소개서', filename: '자기소개서' },
]

const EMPTY_MATERIALS: Record<ResumeDocumentKind, ResumeMaterial[]> = {
  resume: [],
  career: [],
  essay: [],
}

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export function ResumeBuilderPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: seed } = useSuspenseQuery(resumeSeedQuery)
  const existing = id ? getSavedApplication(id) : undefined

  const [applicationId] = useState(() => existing?.id ?? newApplicationId())
  const [title, setTitle] = useState(() => existing?.title ?? '')
  const [documents, setDocuments] = useState<ResumeApplicationDocuments>(
    () => existing?.documents ?? seed,
  )
  const [included, setIncluded] = useState<ResumeDocumentKind[]>(
    () => existing?.included ?? DOCUMENTS.map(({ kind }) => kind),
  )
  const [active, setActive] = useState<ResumeDocumentKind>('resume')
  const [materials, setMaterials] = useState(EMPTY_MATERIALS)
  const [downloadError, setDownloadError] = useState('')

  const current = documents[active]
  const currentMeta = DOCUMENTS.find(({ kind }) => kind === active) ?? DOCUMENTS[0]
  const stateKey = useMemo(() => JSON.stringify(current), [current])
  const { data: html = '' } = useQuery({
    queryKey: ['resume-preview', active, stateKey],
    queryFn: async () => {
      const response = await fetch('/api/resume/preview', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ state: current, kind: active }),
      })
      if (!response.ok) throw new Error('미리보기를 만들지 못했습니다.')
      return response.text()
    },
  })

  const updateCurrent = (update: (state: ResumeState) => ResumeState) =>
    setDocuments((all) => ({ ...all, [active]: update(all[active]) }))

  const save = () => {
    upsertSavedApplication({
      id: applicationId,
      title: title.trim() || '새 입사지원서',
      documents,
      included,
      updatedAt: Date.now(),
    })
    navigate('/resume')
  }

  const download = async (bundle: boolean) => {
    setDownloadError('')
    const path = bundle ? '/api/resume/render-bundle' : '/api/resume/render'
    const body = bundle
      ? { documents, included }
      : { state: current, kind: active }
    try {
      const response = await fetch(path, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!response.ok) throw new Error()
      const base = (title.trim() || '입사지원서').replace(/[\\/:*?"<>|]/g, '-')
      saveBlob(await response.blob(), `${base}${bundle ? '' : `_${currentMeta.filename}`}.pdf`)
    } catch {
      setDownloadError('PDF를 만들지 못했습니다. 잠시 후 다시 시도해 주세요.')
    }
  }

  const toggleIncluded = () =>
    setIncluded((items) =>
      items.includes(active) ? items.filter((kind) => kind !== active) : [...items, active],
    )

  return (
    <div className="application-workspace">
      <header className="application-workspace__header">
        <div className="application-workspace__heading">
          <Button size="sm" variant="ghost" onClick={() => navigate('/resume')}>
            ← 목록
          </Button>
          <input
            className="of-input application-workspace__title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="워크스페이스 이름"
            aria-label="워크스페이스 이름"
          />
        </div>
        <div className="application-workspace__actions">
          <Button variant="ghost" onClick={save}>저장</Button>
          <Button disabled={included.length === 0} onClick={() => download(true)}>
            전체 PDF ↓
          </Button>
        </div>
      </header>

      <nav className="application-doc-tabs" aria-label="입사지원서 문서">
        {DOCUMENTS.map(({ kind, label }) => (
          <button
            key={kind}
            className={kind === active ? 'is-active' : ''}
            aria-pressed={kind === active}
            onClick={() => setActive(kind)}
          >
            {label}
          </button>
        ))}
      </nav>

      <div className="resume-builder">
        <aside className="resume-side">
          <div className="application-doc-head">
            <div>
              <span className="of-mono">현재 문서</span>
              <h3>{currentMeta.label} 편집</h3>
            </div>
            <label>
              <input
                type="checkbox"
                checked={included.includes(active)}
                onChange={toggleIncluded}
              />
              전체 PDF에 포함
            </label>
          </div>

          {active === 'essay' ? (
            <div className="resume-materials">
              <EssaysPanel
                state={current}
                onDoc={(patch) =>
                  updateCurrent((state) => ({ ...state, doc: { ...state.doc, ...patch } }))
                }
              />
            </div>
          ) : (
            <MaterialsPanel
              state={current}
              materials={materials[active]}
              documentLabel={currentMeta.label}
              showTemplate={active === 'resume'}
              onAddMaterial={(material) =>
                setMaterials((all) => ({ ...all, [active]: [...all[active], material] }))
              }
              onTemplate={(style) => updateCurrent((state) => ({ ...state, style }))}
            />
          )}

          <ChatBubble
            state={current}
            materials={materials[active]}
            onState={(state) => updateCurrent(() => state)}
          />
        </aside>

        <section className="resume-preview">
          <div className="resume-preview__header">
            <span>{currentMeta.label} 미리보기</span>
            <Button size="sm" variant="ghost" onClick={() => download(false)}>
              PDF ↓
            </Button>
          </div>
          {downloadError && <p className="form-error">{downloadError}</p>}
          <iframe title={`${currentMeta.label} 미리보기`} srcDoc={html} sandbox="" />
        </section>
      </div>
    </div>
  )
}
