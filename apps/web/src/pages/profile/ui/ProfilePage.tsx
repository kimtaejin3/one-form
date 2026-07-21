import { useSuspenseQuery } from '@tanstack/react-query'
import { Card } from '@one-form/design-system'
import { profileQuery } from '@/entities/profile'
import { UploadResume } from '@/features/upload-resume'

export default function ProfilePage() {
  const { data: profile } = useSuspenseQuery(profileQuery)

  return (
    <div className="stack">
      <UploadResume />

      <Card>
        <div className="stack">
          <strong>개인정보</strong>
          <div className="personal-body">
            <div className="id-photo">증명사진</div>
            <dl className="info-grid">
              <dt>이름</dt>
              <dd>{profile.personal.name}</dd>
              <dt>영문</dt>
              <dd>{profile.personal.name_en}</dd>
              <dt>한자</dt>
              <dd>{profile.personal.name_cn}</dd>
              <dt>주소</dt>
              <dd>{profile.personal.address}</dd>
              <dt>연락처</dt>
              <dd>{profile.personal.phone}</dd>
              <dt>이메일</dt>
              <dd>{profile.personal.email}</dd>
              <dt>비상 연락처</dt>
              <dd>{profile.personal.emergency_phone}</dd>
              <dt>비상 연락처 관계</dt>
              <dd>{profile.personal.emergency_relation}</dd>
            </dl>
          </div>
        </div>
      </Card>

      <Card>
        <div className="stack">
          <strong>학력</strong>
          <div className="resume-list">
            {profile.educations.map((edu) => (
              <div key={edu.school} className="resume-entry">
                <span className="resume-entry__title">
                  {edu.school} <span className="of-chip">{edu.status}</span>
                </span>
                <span className="resume-entry__meta">
                  {edu.major} · {edu.period}
                  {edu.gpa && ` · 학점 ${edu.gpa}`}
                </span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="stack">
          <strong>경력</strong>
          <div className="resume-list">
            {profile.careers.map((c) => (
              <div key={c.company} className="resume-entry">
                <span className="resume-entry__title">
                  {c.company} <span className="of-chip">{c.role}</span>
                </span>
                <span className="resume-entry__meta">{c.period}</span>
                <ul className="resume-entry__list">
                  {c.highlights.map((h) => (
                    <li key={h}>{h}</li>
                  ))}
                </ul>
                <div className="row">
                  {c.stack.map((s) => (
                    <span key={s} className="of-chip">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="stack">
          <strong>프로젝트</strong>
          <div className="resume-list">
            {profile.projects.map((p) => (
              <div key={p.name} className="resume-entry">
                <span className="resume-entry__title">{p.name}</span>
                <span className="resume-entry__meta">
                  {p.role} · {p.period}
                </span>
                <span className="resume-entry__desc">{p.summary}</span>
                <ul className="resume-entry__list">
                  {p.highlights.map((h) => (
                    <li key={h}>{h}</li>
                  ))}
                </ul>
                <div className="row">
                  {p.stack.map((s) => (
                    <span key={s} className="of-chip">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="stack">
          <strong>자격증</strong>
          <div className="resume-list">
            {profile.certificates.map((c) => (
              <div key={c.name} className="resume-entry">
                <span className="resume-entry__title">{c.name}</span>
                <span className="resume-entry__meta">
                  {c.issuer} · {c.date} 취득
                </span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="stack">
          <strong>어학</strong>
          <div className="resume-list">
            {profile.languages.map((lang) => (
              <div key={lang.test} className="resume-entry">
                <span className="resume-entry__title">
                  {lang.language} · {lang.test}
                </span>
                <span className="resume-entry__meta">
                  {lang.score} · {lang.date} 취득
                </span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="stack">
          <strong>수상</strong>
          <div className="resume-list">
            {profile.awards.map((aw) => (
              <div key={aw.title} className="resume-entry">
                <span className="resume-entry__title">{aw.title}</span>
                <span className="resume-entry__meta">
                  {aw.org} · {aw.date}
                </span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="stack">
          <strong>대외활동 / 교육</strong>
          <div className="resume-list">
            {profile.activities.map((a) => (
              <div key={a.title} className="resume-entry">
                <span className="resume-entry__title">
                  <span className="of-chip">{a.type}</span> {a.title}
                </span>
                <span className="resume-entry__meta">
                  {a.org} · {a.period}
                </span>
                <span className="resume-entry__desc">{a.description}</span>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  )
}
