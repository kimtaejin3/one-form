import type { Intelligence, Signal } from '@/features/analyze-company'
import { SourceRefs, type SourceMap } from './evidence'

const SIGNAL_LABEL: Record<Signal['signal_type'], string> = {
  business: '사업',
  product: '제품',
  hiring: '채용',
  technology: '기술',
  risk: '리스크',
  culture: '조직문화',
}

export default function SignalTimeline({
  signals,
  sources,
}: {
  signals: Intelligence['signals']
  sources: SourceMap
}) {
  if (signals.length === 0) {
    return <p className="brief-empty">확인된 최근 신호가 없습니다.</p>
  }
  return (
    <div className="stack">
      {signals.map((s) => (
        <div key={s.label} className="signal">
          <span className="signal__label">
            {SIGNAL_LABEL[s.signal_type]} · {s.label}
          </span>
          <p>{s.detail}</p>
          {s.evidence_quote && <blockquote>“{s.evidence_quote}”</blockquote>}
          <div className="row signal__source">
            <SourceRefs ids={s.source_ids} sources={sources} />
          </div>
        </div>
      ))}
    </div>
  )
}
