import { Button, Card } from '@one-form/design-system'
import type { Intelligence } from '@/features/analyze-company'
import { Fact, SourceRefs, type SourceMap } from './evidence'

function when(iso: string | null) {
  return iso ? new Date(iso).toLocaleString('ko-KR') : '—'
}

export default function CompanyOverviewCard({
  brief,
  sources,
  onRefresh,
  refreshing,
}: {
  brief: Intelligence
  sources: SourceMap
  onRefresh: () => void
  refreshing: boolean
}) {
  return (
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
          {brief.summary ? (
            <>
              <p className="brief-summary">{brief.summary.text}</p>
              <SourceRefs ids={brief.summary.source_ids} sources={sources} />
            </>
          ) : (
            <p className="brief-summary">확인된 출처에서 요약을 만들지 못했습니다.</p>
          )}
          {brief.stage && (
            <div className="row">
              <Fact fact={brief.stage} sources={sources} />
            </div>
          )}
        </div>
      </div>
      <dl className="brief-meta">
        <div>
          <dt>분석 시각</dt>
          <dd>{when(brief.last_analyzed_at)}</dd>
        </div>
        <div>
          <dt>최신성 유지</dt>
          <dd>{when(brief.fresh_until)}까지</dd>
        </div>
        <div>
          <dt>출처</dt>
          <dd>{brief.source_count}건</dd>
        </div>
      </dl>
      <Button type="button" disabled={refreshing} onClick={onRefresh}>
        다시 분석
      </Button>
    </Card>
  )
}
