import { Link } from 'react-router-dom'
import { listSavedApplications } from '@/entities/resume'
import { Icon } from '@/shared/ui'

export default function HomePage() {
  const applicationCount = listSavedApplications().length

  return (
    <div className="home-hub">
      <section className="home-primary">
        <div className="home-primary__copy">
          <span className="of-mono">ONEFORM APPLICATION WORKSPACE</span>
          <h1>입사지원서 작성부터 PDF 제출까지 한 곳에서</h1>
          <p>
            마스터 프로필을 바탕으로 이력서·경력기술서·자기소개서를 만들고,
            필요한 문서만 묶어 제출용 PDF로 내려받으세요.
          </p>
          <div className="home-actions">
            <Link to="/resume/new" className="of-btn">새 입사지원서</Link>
            {applicationCount > 0 && (
              <Link to="/resume" className="of-btn of-btn--ghost">
                내 입사지원서 {applicationCount}개
              </Link>
            )}
          </div>
        </div>
        <div className="home-docs" aria-label="입사지원서 구성 문서">
          <span>이력서</span>
          <span>경력기술서</span>
          <span>자기소개서</span>
          <strong>전체 PDF</strong>
        </div>
      </section>

      <section className="home-core" aria-label="핵심 기능">
        <Link to="/profile" className="home-feature">
          <Icon name="person" size={24} />
          <div><strong>마스터 프로필</strong><p>한 번 정리한 경력과 프로젝트를 모든 문서에 재사용합니다.</p></div>
          <span>열기 →</span>
        </Link>
        <Link to="/forms" className="home-feature">
          <Icon name="transform" size={24} />
          <div><strong>양식 변환</strong><p>보유한 지원서 정보를 기업 양식에 맞춰 변환합니다.</p></div>
          <span>열기 →</span>
        </Link>
      </section>

      <Link to="/jobs" className="home-jobs">
        <div className="home-jobs__icon"><Icon name="work" size={24} /></div>
        <div>
          <span className="of-mono">PROFILE MATCHING</span>
          <h2>내 경험과 맞는 채용공고 추천</h2>
          <p>마스터 프로필과 공고의 직무·기술 요건을 비교해 적합도와 근거를 확인합니다.</p>
        </div>
        <strong>추천 공고 보기 →</strong>
      </Link>
    </div>
  )
}
