import { useState, type FormEvent } from 'react'
import { Button, Input } from '@one-form/design-system'

/** 기업명 + (선택) 공고 URL. 제출만 담당하고 결과 표시는 위젯이 한다. */
export default function CompanySearchForm({
  onSubmit,
  pending,
}: {
  onSubmit: (name: string, jobUrl?: string) => void
  pending: boolean
}) {
  const [name, setName] = useState('')
  const [jobUrl, setJobUrl] = useState('')

  function submit(e: FormEvent) {
    e.preventDefault()
    if (name.trim()) onSubmit(name, jobUrl.trim() || undefined)
  }

  return (
    <form className="stack" onSubmit={submit} style={{ maxWidth: 560 }}>
      <div className="row">
        <Input
          placeholder="기업명 입력 (예: 쿠팡)"
          aria-label="기업명"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ flex: 1, width: 'auto' }}
        />
        <Button disabled={pending}>{pending ? '분석 중…' : '분석'}</Button>
      </div>
      <Input
        placeholder="채용공고 URL (선택) — 직무 분석과 내 경험 매칭에 쓰입니다"
        aria-label="채용공고 URL"
        value={jobUrl}
        onChange={(e) => setJobUrl(e.target.value)}
      />
    </form>
  )
}
