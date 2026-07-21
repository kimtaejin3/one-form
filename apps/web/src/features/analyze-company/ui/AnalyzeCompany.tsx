import { useState, type FormEvent } from 'react'
import { Button, Card, Input } from '@one-form/design-system'
import { useAnalyzeCompany } from '../model'

export default function AnalyzeCompany() {
  const [name, setName] = useState('')
  const analyze = useAnalyzeCompany()
  const brief = analyze.data

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (name.trim()) analyze.mutate(name)
  }

  return (
    <div className="stack">
      <form className="row" onSubmit={onSubmit} style={{ maxWidth: 480 }}>
        <Input
          placeholder="기업명 입력 (예: 쿠팡)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ flex: 1, width: 'auto' }}
        />
        <Button disabled={analyze.isPending}>{analyze.isPending ? '분석 중…' : '분석'}</Button>
      </form>
      {brief && (
        <>
          <Card>
            <div className="stack">
              <strong>{brief.name} — 분석 브리프</strong>
              <span className="of-mono">사업 영역</span>
              <div className="row">
                {brief.business_areas.map((b) => (
                  <span key={b} className="of-chip">
                    {b}
                  </span>
                ))}
              </div>
              <span className="of-mono">대표 제품 / 서비스</span>
              <div className="row">
                {brief.products.map((p) => (
                  <span key={p} className="of-chip">
                    {p}
                  </span>
                ))}
              </div>
              <span className="of-mono">JD 요구 역량</span>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {brief.jd_skills.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          </Card>
          <Card>
            <strong>강점 매칭 보드</strong>
            <table className="data-table" style={{ marginTop: 12 }}>
              <thead>
                <tr>
                  <th>기업 과제</th>
                  <th>내 경험</th>
                  <th>적합도</th>
                </tr>
              </thead>
              <tbody>
                {brief.strength_matching.map((m) => (
                  <tr key={m.company_issue}>
                    <td>{m.company_issue}</td>
                    <td>{m.my_experience}</td>
                    <td>
                      <span className="of-chip">{m.fit}%</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </div>
  )
}
