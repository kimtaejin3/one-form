import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@one-form/design-system'
import { listSavedDocs, removeSavedDoc, type SavedDoc } from '@/entities/resume'

// 저장한 이력서·포트폴리오를 모아 보여주고, 골라서 열거나 새로 만든다.
export function ResumeGalleryPage() {
  const navigate = useNavigate()
  const [docs, setDocs] = useState<SavedDoc[]>(() => listSavedDocs())

  const remove = (id: string) => {
    removeSavedDoc(id)
    setDocs(listSavedDocs())
  }

  return (
    <div className="resume-gallery">
      <div className="resume-gallery__head">
        <h2>내 이력서 · 포트폴리오</h2>
        <div className="resume-gallery__new">
          <Button onClick={() => navigate('/resume/new?kind=resume')}>+ 새 이력서</Button>
          <Button variant="ghost" onClick={() => navigate('/resume/new?kind=portfolio')}>
            + 새 포트폴리오
          </Button>
        </div>
      </div>

      {docs.length === 0 ? (
        <div className="resume-gallery__empty">
          아직 만든 문서가 없습니다. <strong>새 이력서</strong>로 시작해 보세요.
        </div>
      ) : (
        <div className="resume-gallery__grid">
          {docs.map((d) => (
            <div key={d.id} className="resume-doc-card">
              <Link to={`/resume/edit/${d.id}`} className="resume-doc-card__body">
                <span className={`resume-doc-card__badge is-${d.kind}`}>
                  {d.kind === 'portfolio' ? '포트폴리오' : '이력서'}
                </span>
                <strong className="resume-doc-card__title">{d.title}</strong>
                <span className="resume-doc-card__meta">
                  {new Date(d.updatedAt).toLocaleString('ko-KR', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </Link>
              <button className="resume-doc-card__del" onClick={() => remove(d.id)}>
                삭제
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
