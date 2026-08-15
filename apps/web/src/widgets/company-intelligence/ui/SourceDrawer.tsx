import { Card } from '@one-form/design-system'
import type { Intelligence } from '@/features/analyze-company'
import { SourceChip } from './evidence'

/** 하단 출처 목록 + 면책 문구(계획서 §8·§11). */
export default function SourceDrawer({ brief }: { brief: Intelligence }) {
  const changed = brief.sources.filter((s) => s.changed).length

  return (
    <Card>
      <div className="stack">
        <strong>출처 {brief.source_count > 0 && `(${brief.source_count})`}</strong>
        {brief.sources.length === 0 && <p className="brief-empty">수집된 출처가 없습니다.</p>}
        <ul className="brief-list">
          {brief.sources.map((s) => (
            <li key={s.id}>
              <SourceChip source={s} />{' '}
              <a href={s.url} target="_blank" rel="noopener noreferrer">
                {s.title || s.url}
              </a>
            </li>
          ))}
        </ul>
        {changed > 0 && (
          <span className="of-mono">직전 분석 이후 원문이 바뀐 출처 {changed}건이 있습니다.</span>
        )}
        {brief.manual_urls.length > 0 && (
          <span className="of-mono">
            등록한 공고 URL {brief.manual_urls.length}건은 다시 분석할 때도 유지됩니다.
          </span>
        )}
        <p className="of-mono disclaimer">
          출처 기반 참고 정보입니다. 투자·법률 조언이나 합격 가능성 판단이 아닙니다.
        </p>
      </div>
    </Card>
  )
}
