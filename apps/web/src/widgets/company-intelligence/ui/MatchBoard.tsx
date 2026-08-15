import { useCompanyMatches, type CompanyJob } from '@/features/analyze-company'
import { SourceRefs, type SourceMap } from './evidence'

/** 기업 요구 → 내 경험 → 근거. 점수보다 설명이 먼저다(계획서 §8). */
export default function MatchBoard({
  normalizedName,
  job,
  sources,
}: {
  normalizedName: string
  job: CompanyJob | null
  sources: SourceMap
}) {
  const matches = useCompanyMatches(normalizedName, job?.id)

  if (!job) {
    return (
      <p className="brief-empty">
        채용공고 URL을 입력하면 그 직무의 요구 역량과 내 경험을 대조해드려요.
      </p>
    )
  }
  if (matches.isPending) return <p className="of-mono">내 경험과 대조하는 중…</p>
  if (matches.isError) return <p className="of-mono">매칭을 불러오지 못했습니다.</p>

  const rows = matches.data ?? []
  if (rows.length === 0) {
    return (
      <p className="brief-empty">
        마스터 프로필이 등록되면 이 공고의 요구 역량과 내 경험을 대조해 보여드려요.
      </p>
    )
  }

  const strengths = rows.filter((m) => m.match_type === 'strength')
  const gaps = rows.filter((m) => m.match_type === 'gap')

  return (
    <div className="stack">
      <span className="of-mono">
        강점 {strengths.length} · 갭 {gaps.length}
      </span>
      {rows.map((m) => (
        <div key={`${m.match_type}-${m.company_need}`} className={`match match--${m.match_type}`}>
          <div className="match__head">
            <span className="match__need">{m.company_need}</span>
            <span className="match__badge">{m.match_type === 'strength' ? '강점' : '갭'}</span>
            {m.match_type === 'strength' && <span className="match__score">{m.score}%</span>}
          </div>
          {m.profile_evidence && (
            <p className="match__evidence">
              <span className="of-mono">내 경험</span> {m.profile_evidence}
            </p>
          )}
          <p className="match__reason">{m.reason}</p>
          <SourceRefs ids={m.source_ids} sources={sources} />
        </div>
      ))}
    </div>
  )
}
