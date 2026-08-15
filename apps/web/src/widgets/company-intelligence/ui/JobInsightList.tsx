import type { CompanyJob } from '@/features/analyze-company'
import { SourceRefs, type SourceMap } from './evidence'

export default function JobInsightList({
  jobs,
  selected,
  onSelect,
  sources,
}: {
  jobs: CompanyJob[]
  selected: CompanyJob | null
  onSelect: (id: number) => void
  sources: SourceMap
}) {
  if (!selected) {
    return (
      <p className="brief-empty">
        채용공고 URL을 입력하면 직무별 핵심 역량과 문제 유형을 정리해드려요.
      </p>
    )
  }

  const lists: [string, string[]][] = [
    ['핵심 역량', selected.core_skills],
    ['문제 유형', selected.problem_types],
    ['자격 요건', selected.requirements],
    ['우대 사항', selected.preferred],
  ]

  return (
    <div className="stack">
      {jobs.length > 1 && (
        <div className="row" role="tablist" aria-label="공고 선택">
          {jobs.map((j) => (
            <button
              key={j.id}
              type="button"
              role="tab"
              aria-selected={j.id === selected.id}
              className={`of-chip job-tab${j.id === selected.id ? ' job-tab--on' : ''}`}
              onClick={() => onSelect(j.id)}
            >
              {j.title}
            </button>
          ))}
        </div>
      )}
      <strong className="job-insight__title">{selected.title}</strong>
      <div className="job-insight__meta">
        <span className="of-mono">
          {[selected.role_category, selected.location, selected.employment, selected.deadline]
            .filter(Boolean)
            .join(' · ')}
        </span>
        <SourceRefs ids={[selected.source_id]} sources={sources} />
      </div>
      {selected.description && <p>{selected.description}</p>}
      {lists.map(([label, values]) =>
        values.length > 0 ? (
          <div key={label}>
            <span className="of-mono">{label}</span>
            <div className="row">
              {values.map((v) => (
                <span key={v} className="of-chip">
                  {v}
                </span>
              ))}
            </div>
          </div>
        ) : null,
      )}
    </div>
  )
}
