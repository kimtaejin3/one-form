import { useState, type FormEvent } from 'react'
import { Button, Card, Input } from '@one-form/design-system'
import { useAnalyzeCompany } from '../model'

function FitBar({ value }: { value: number }) {
  return (
    <div className="fit">
      <div className="fit__track">
        <div className="fit__fill" style={{ width: `${value}%` }} />
      </div>
      <span className="fit__val">{value}%</span>
    </div>
  )
}

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

      {!brief && !analyze.isPending && (
        <Card>
          <div className="brief-empty">
            <p>기업명을 입력하면 사업·최근 동향·예상 면접 포인트와 내 경험 적합도를 브리핑해드려요.</p>
            <span className="of-mono">예: 쿠팡 · 네이버 · 토스</span>
          </div>
        </Card>
      )}

      {brief && (
        <>
          <Card>
            <div className="brief-header">
              <div className="brief-logo">
                {brief.domain ? (
                  <img
                    src={`https://www.google.com/s2/favicons?domain=${brief.domain}&sz=128`}
                    alt=""
                    width={40}
                    height={40}
                  />
                ) : (
                  brief.name.slice(0, 2)
                )}
              </div>
              <div>
                <strong className="brief-name">{brief.name}</strong>
                <p className="brief-summary">{brief.summary}</p>
                <span className="of-chip">{brief.stage}</span>
              </div>
            </div>
          </Card>

          <Card>
            <div className="stack">
              <strong>개요</strong>
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
              <ul className="brief-list">
                {brief.jd_skills.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          </Card>

          <Card>
            <div className="stack">
              <strong>최근 동향</strong>
              {brief.signals.map((s) => (
                <div key={s.label} className="signal">
                  <span className="signal__label">{s.label}</span>
                  <p>{s.detail}</p>
                  <span className="signal__source">근거: {s.source}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <div className="stack">
              <strong>내 경험 강점 매칭</strong>
              {brief.strength_matching.map((m) => (
                <div key={m.company_issue} className="strength">
                  <div className="strength__text">
                    <p>
                      <span className="of-mono">기업 과제</span> {m.company_issue}
                    </p>
                    <p>
                      <span className="of-mono">내 경험</span> {m.my_experience}
                    </p>
                  </div>
                  <FitBar value={m.fit} />
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <div className="stack">
              <strong>예상 면접 포인트</strong>
              {brief.interview_points.map((p) => (
                <div key={p.question} className="qa">
                  <p className="qa__q">Q. {p.question}</p>
                  <p className="qa__hint">{p.hint}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <div className="stack">
              <strong>지원 팁</strong>
              <ul className="brief-list">
                {brief.apply_tips.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
