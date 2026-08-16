import { useState } from 'react'
import { Button, Card, Input } from '@one-form/design-system'
import type { ProfileData } from '@/entities/profile'
import { useSaveProfile } from '../model'

type Props = { profile: ProfileData; onCancel: () => void; onSaved: () => void }

type ListKey = 'links' | 'educations' | 'careers' | 'projects' | 'certificates' | 'languages' | 'awards' | 'activities' | 'skill_groups' | 'open_source_contributions'
type ProfileItem = Record<string, string | string[]>

const LIST_SECTIONS: { key: ListKey; title: string; empty: ProfileItem }[] = [
  { key: 'links', title: '링크', empty: { label: '', url: '' } },
  { key: 'educations', title: '학력', empty: { school: '', major: '', period: '', status: '', gpa: '' } },
  { key: 'careers', title: '경력', empty: { company: '', role: '', period: '', highlights: [], stack: [] } },
  { key: 'projects', title: '프로젝트', empty: { name: '', organization: '', role: '', period: '', summary: '', highlights: [], stack: [] } },
  { key: 'certificates', title: '자격증', empty: { name: '', issuer: '', date: '' } },
  { key: 'languages', title: '어학', empty: { language: '', test: '', score: '', date: '' } },
  { key: 'awards', title: '수상', empty: { title: '', org: '', date: '' } },
  { key: 'activities', title: '대외활동 / 교육', empty: { type: '', title: '', org: '', period: '', description: '' } },
  { key: 'skill_groups', title: '기술', empty: { category: '', skills: [] } },
  { key: 'open_source_contributions', title: '오픈소스 기여', empty: { repository: '', url: '', highlights: [] } },
]

export default function ProfileEditor({ profile, onCancel, onSaved }: Props) {
  const save = useSaveProfile()
  const [personal, setPersonal] = useState(profile.personal)
  const [sections, setSections] = useState(() => Object.fromEntries(
    LIST_SECTIONS.map(({ key }) => [key, (profile[key] ?? []) as unknown as ProfileItem[]]),
  ) as Record<ListKey, ProfileItem[]>)
  const [error, setError] = useState('')

  function submit(event: React.FormEvent) {
    event.preventDefault()
    setError('')
    save.mutate(
      { ...profile, registered: true, personal, ...sections } as ProfileData,
      { onSuccess: onSaved, onError: () => setError('저장하지 못했습니다. 입력 내용을 확인해 주세요.') },
    )
  }

  function updateItem(section: ListKey, index: number, field: string, value: string | string[]) {
    const items = sections[section].map((item, itemIndex) => (
      itemIndex === index ? { ...item, [field]: value } : item
    ))
    setSections({ ...sections, [section]: items })
  }

  return (
    <Card>
      <form className="profile-editor" onSubmit={submit}>
        <div className="profile-editor__heading">
          <div>
            <h2>마스터 프로필 편집</h2>
            <p>업로드 결과를 검토하고 필요한 항목을 수정한 뒤 저장하세요.</p>
          </div>
          <div className="row">
            <Button type="button" variant="ghost" onClick={onCancel}>취소</Button>
            <Button type="submit" disabled={save.isPending}>{save.isPending ? '저장 중…' : '저장'}</Button>
          </div>
        </div>

        <section>
          <h3 className="resume-section__title">개인정보</h3>
          <div className="profile-editor__personal">
            {Object.entries(personal).map(([key, value]) => (
              <label key={key}>
                <span>{PERSONAL_LABELS[key] ?? key}</span>
                <Input value={value} onChange={(event) => setPersonal({ ...personal, [key]: event.target.value })} />
              </label>
            ))}
          </div>
        </section>

        {LIST_SECTIONS.map(({ key, title }) => (
          <section key={key}>
            <h3 className="resume-section__title">{title}</h3>
            <div className="profile-editor__list">
              {sections[key].map((item, index) => (
                <div className="profile-editor__entry" key={`${key}-${index}`}>
                  <div className="profile-editor__fields">
                    {Object.entries(item).map(([field, value]) => (
                      <label key={field}>
                        <span>{FIELD_LABELS[field] ?? field}</span>
                        <Input
                          value={Array.isArray(value) ? value.join(', ') : value}
                          placeholder={Array.isArray(value) ? '쉼표로 구분' : ''}
                          onChange={(event) => updateItem(
                            key,
                            index,
                            field,
                            Array.isArray(value)
                              ? event.target.value.split(',').map((item) => item.trim()).filter(Boolean)
                              : event.target.value,
                          )}
                        />
                      </label>
                    ))}
                  </div>
                  <Button type="button" variant="ghost" size="sm" onClick={() => setSections({
                    ...sections, [key]: sections[key].filter((_, itemIndex) => itemIndex !== index),
                  })}>삭제</Button>
                </div>
              ))}
              <Button type="button" variant="ghost" size="sm" onClick={() => setSections({
                ...sections, [key]: [...sections[key], { ...LIST_SECTIONS.find((section) => section.key === key)!.empty }],
              })}>{title} 추가</Button>
            </div>
          </section>
        ))}
        {error && <p className="form-error">{error}</p>}
      </form>
    </Card>
  )
}

const PERSONAL_LABELS: Record<string, string> = {
  photo: '사진 URL', name: '이름', name_en: '영문 이름', name_cn: '한자 이름', address: '주소',
  headline: '직무 제목', summary: '소개', phone: '연락처', email: '이메일', emergency_phone: '비상 연락처', emergency_relation: '관계',
}

const FIELD_LABELS: Record<string, string> = {
  label: '이름', url: 'URL', school: '학교', major: '전공', period: '기간', status: '상태', gpa: '학점',
  company: '회사', role: '역할', highlights: '주요 성과', stack: '기술 스택', name: '이름', summary: '설명',
  issuer: '발급 기관', date: '일자', language: '언어', test: '시험', score: '점수', title: '제목',
  org: '기관', type: '유형', description: '설명', category: '분류', skills: '기술', repository: '저장소', organization: '소속',
}
