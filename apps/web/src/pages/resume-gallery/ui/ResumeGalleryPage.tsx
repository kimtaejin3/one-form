import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@one-form/design-system'
import {
  listSavedApplications,
  removeSavedApplication,
  type SavedApplication,
} from '@/entities/resume'

// 한 워크스페이스에서 이력서·경력기술서·자기소개서를 함께 관리한다.
export function ResumeGalleryPage() {
  const navigate = useNavigate()
  const [applications, setApplications] = useState<SavedApplication[]>(
    () => listSavedApplications(),
  )

  const remove = (id: string) => {
    removeSavedApplication(id)
    setApplications(listSavedApplications())
  }

  return (
    <div className="resume-gallery">
      <div className="resume-gallery__head">
        <div>
          <h2>입사지원서 빌더</h2>
          <p>이력서·경력기술서·자기소개서를 한 곳에서 관리하세요.</p>
        </div>
        <div className="resume-gallery__new">
          <Button onClick={() => navigate('/resume/new')}>+ 새 입사지원서</Button>
        </div>
      </div>

      {applications.length === 0 ? (
        <div className="resume-gallery__empty">
          아직 만든 입사지원서가 없습니다. <strong>새 입사지원서</strong>로 시작해 보세요.
        </div>
      ) : (
        <div className="resume-gallery__grid">
          {applications.map((application) => (
            <div key={application.id} className="resume-doc-card">
              <Link to={`/resume/edit/${application.id}`} className="resume-doc-card__body">
                <span className="resume-doc-card__badge">입사지원서</span>
                <strong className="resume-doc-card__title">{application.title}</strong>
                <span className="resume-doc-card__documents">
                  이력서 · 경력기술서 · 자기소개서
                </span>
                <span className="resume-doc-card__meta">
                  {new Date(application.updatedAt).toLocaleString('ko-KR', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </Link>
              <button className="resume-doc-card__del" onClick={() => remove(application.id)}>
                삭제
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
