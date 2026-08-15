import type { Source, SourcedText } from '@/features/analyze-company'

export type SourceMap = Map<number, Source>

const TRUST_LABEL: Record<Source['trust_level'], string> = {
  primary: '공식',
  secondary: '보조',
  user_provided: '직접 입력',
}

/** 출처 칩 — 원문 링크는 항상 새 탭, 출처 도메인을 함께 보여준다(계획서 §8). */
export function SourceChip({ source }: { source: Source }) {
  return (
    <a
      className="of-chip source-chip"
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      title={source.title || source.url}
    >
      [{source.id}] {source.publisher} · {TRUST_LABEL[source.trust_level]}
      {source.changed && <span className="source-chip__changed"> 변경됨</span>}
    </a>
  )
}

export function SourceRefs({ ids, sources }: { ids: number[]; sources: SourceMap }) {
  return (
    <span className="source-refs">
      {ids.map((id) => {
        const source = sources.get(id)
        return source ? <SourceChip key={id} source={source} /> : null
      })}
    </span>
  )
}

/** 사실 한 조각 + 근거. 근거 없는 값은 애초에 서버가 내려주지 않는다. */
export function Fact({ fact, sources }: { fact: SourcedText; sources: SourceMap }) {
  return (
    <span className="fact">
      <span className="of-chip">{fact.text}</span>
      <SourceRefs ids={fact.source_ids} sources={sources} />
    </span>
  )
}
