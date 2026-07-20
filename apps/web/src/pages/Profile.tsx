import { useSuspenseQuery, useMutation } from '@tanstack/react-query'
import { Card } from '@one-form/design-system'
import { post } from '../api'
import { profileQuery } from '../queries/profile'

export default function Profile() {
  const { data: profile } = useSuspenseQuery(profileQuery)
  const resume = useMutation({ mutationFn: () => post<{ message: string }>('/profile/resume') })

  return (
    <div className="stack">
      <div className="row" style={{ marginBottom: 10 }}>
        <label className="of-btn of-btn--sm">
          {resume.isPending ? '분석 중…' : '이력서 업로드'}
          <input
            type="file"
            hidden
            accept=".pdf,.docx,.hwp"
            onChange={() => resume.mutate()}
            disabled={resume.isPending}
          />
        </label>
        {resume.data && <span className="of-mono">{resume.data.message}</span>}
      </div>

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
          {profile.educations.map((edu) => (
            <div key={edu.school} className="stack" style={{ gap: 2 }}>
              <span>
                {edu.school} <span className="of-chip">{edu.status}</span>
              </span>
              <span className="of-mono">
                {edu.period} · {edu.note}
              </span>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <div className="stack">
          <strong>어학</strong>
          {profile.languages.map((lang) => (
            <div key={lang.test} className="row">
              <span>{lang.name}</span>
              <span className="of-mono">
                {lang.test} · {lang.score}
              </span>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <div className="stack">
          <strong>수상</strong>
          {profile.awards.map((aw) => (
            <div key={aw.title} className="stack" style={{ gap: 2 }}>
              <span>{aw.title}</span>
              <span className="of-mono">
                {aw.org} · {aw.date}
              </span>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <div className="stack">
          <strong>자격증</strong>
          <div className="row">
            {profile.certificates.map((c) => (
              <span key={c} className="of-chip">
                {c}
              </span>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="stack">
          <strong>경험 / 활동 / 교육</strong>
          {profile.career.map((c) => (
            <div key={c.title} className="stack" style={{ gap: 2 }}>
              <span>
                <span className="of-chip">{c.type}</span> {c.title}
              </span>
              <span className="of-mono">
                {c.org} · {c.period}
              </span>
              <span>{c.description}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
