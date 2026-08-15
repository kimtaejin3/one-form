import { useState } from 'react'
import { Card } from '@one-form/design-system'
import { CompanySearchForm, useAnalyzeCompany } from '@/features/analyze-company'
import AnalysisStatus from './AnalysisStatus'
import CompanyOverviewCard from './CompanyOverviewCard'
import JobInsightList from './JobInsightList'
import MatchBoard from './MatchBoard'
import SignalTimeline from './SignalTimeline'
import SourceDrawer from './SourceDrawer'
import { Fact, type SourceMap } from './evidence'

const TABS = [
  { id: 'business', label: '사업/제품' },
  { id: 'signals', label: '최근 신호' },
  { id: 'jobs', label: '직무 분석' },
  { id: 'matches', label: '내 경험 매칭' },
] as const

type TabId = (typeof TABS)[number]['id']

export default function CompanyIntelligence() {
  const [tab, setTab] = useState<TabId>('business')
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const analyze = useAnalyzeCompany()
  const brief = analyze.data
  const sources: SourceMap = new Map(brief?.sources.map((s) => [s.id, s]))

  // 선택한 공고가 재분석으로 사라지면 첫 공고로 — 렌더 중 파생, useEffect 불필요.
  const selectedJob = brief?.jobs.find((j) => j.id === selectedJobId) ?? brief?.jobs[0] ?? null

  return (
    <div className="stack">
      <CompanySearchForm
        pending={analyze.isPending}
        onSubmit={(name, jobUrl) => analyze.mutate({ name, job_url: jobUrl })}
      />

      {!brief && !analyze.isPending && !analyze.isError && (
        <Card>
          <div className="brief-empty">
            <p>
              기업명을 입력하면 공식 출처를 수집해 사업·제품·최근 신호를 근거 링크와 함께
              정리해드려요. 채용공고 URL을 넣으면 직무 분석과 내 경험 매칭까지 이어집니다.
            </p>
            <span className="of-mono">예: 쿠팡 · 네이버 · 토스</span>
          </div>
        </Card>
      )}

      {analyze.isError && !brief && (
        <Card>
          <p className="brief-empty">분석 요청이 실패했습니다. 잠시 후 다시 시도해 주세요.</p>
        </Card>
      )}

      {brief && (
        <>
          <AnalysisStatus brief={brief} />
          <CompanyOverviewCard
            brief={brief}
            sources={sources}
            refreshing={analyze.isPending}
            onRefresh={() => analyze.mutate({ name: brief.name, force_refresh: true })}
          />

          <div className="tabs" role="tablist" aria-label="기업 정보 보기">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={tab === t.id}
                className={`tab${tab === t.id ? ' tab--on' : ''}`}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>

          <Card>
            <div className="stack" role="tabpanel">
              {tab === 'business' &&
                (brief.business_areas.length + brief.products.length === 0 ? (
                  <p className="brief-empty">확인된 사업·제품 정보가 없습니다.</p>
                ) : (
                  <>
                    {brief.business_areas.length > 0 && (
                      <>
                        <span className="of-mono">사업 영역</span>
                        <div className="row">
                          {brief.business_areas.map((b) => (
                            <Fact key={b.text} fact={b} sources={sources} />
                          ))}
                        </div>
                      </>
                    )}
                    {brief.products.length > 0 && (
                      <>
                        <span className="of-mono">대표 제품 / 서비스</span>
                        <div className="row">
                          {brief.products.map((p) => (
                            <Fact key={p.text} fact={p} sources={sources} />
                          ))}
                        </div>
                      </>
                    )}
                  </>
                ))}

              {tab === 'signals' && <SignalTimeline signals={brief.signals} sources={sources} />}

              {tab === 'jobs' && (
                <JobInsightList
                  jobs={brief.jobs}
                  selected={selectedJob}
                  onSelect={setSelectedJobId}
                  sources={sources}
                />
              )}

              {tab === 'matches' && (
                <MatchBoard
                  normalizedName={brief.normalized_name}
                  job={selectedJob}
                  sources={sources}
                />
              )}
            </div>
          </Card>

          <SourceDrawer brief={brief} />
        </>
      )}
    </div>
  )
}
