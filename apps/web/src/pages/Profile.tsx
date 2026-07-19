import { useState } from 'react'
import { Card } from '@one-form/design-system'
import { post } from '../api'
import { useApi } from '../useApi'

type Experience = {
  id: number
  title: string
  situation: string
  task: string
  action: string
  result: string
  tags: string[]
}

type ProfileData = {
  name: string
  email: string
  education: string
  certificates: string[]
  experiences: Experience[]
}

export default function Profile() {
  const profile = useApi<ProfileData>('/profile')
  const [uploadMsg, setUploadMsg] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)

  async function onUpload() {
    setUploading(true)
    setUploadMsg(null)
    const res = await post<{ message: string }>('/profile/resume')
    setUploadMsg(res.message)
    setUploading(false)
  }

  return (
    <>
      <h2 className="of-h2">마스터 프로필</h2>
      <p className="page-desc">이력서를 업로드하면 핵심 필드를 정규화해 통합 저장소에 적재합니다.</p>
      <div className="row" style={{ marginBottom: 24 }}>
        <label className="of-btn of-btn--sm">
          {uploading ? '분석 중…' : '이력서 업로드'}
          <input type="file" hidden accept=".pdf,.docx,.hwp" onChange={onUpload} disabled={uploading} />
        </label>
        {uploadMsg && <span className="of-mono">{uploadMsg}</span>}
      </div>
      {!profile ? (
        <p className="of-mono">불러오는 중…</p>
      ) : (
        <div className="stack">
          <Card>
            <div className="stack">
              <strong>{profile.name}</strong>
              <span className="of-mono">{profile.email}</span>
              <span>{profile.education}</span>
              <div className="row">
                {profile.certificates.map((c) => (
                  <span key={c} className="of-chip">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </Card>
          <h3 className="of-mono">STAR 경험 · {profile.experiences.length}</h3>
          {profile.experiences.map((exp) => (
            <Card key={exp.id}>
              <div className="stack">
                <strong>{exp.title}</strong>
                <span>
                  <b>S</b> {exp.situation} · <b>T</b> {exp.task}
                </span>
                <span>
                  <b>A</b> {exp.action}
                </span>
                <span>
                  <b>R</b> {exp.result}
                </span>
                <div className="row">
                  {exp.tags.map((t) => (
                    <span key={t} className="of-chip">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </>
  )
}
