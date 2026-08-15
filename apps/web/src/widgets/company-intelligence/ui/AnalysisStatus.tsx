import type { Intelligence } from '@/features/analyze-company'

const STATUS_TEXT: Record<Intelligence['status'], string> = {
  queued: '분석 대기 중',
  collecting: '출처 수집 중',
  analyzing: '분석 중',
  ready: '분석 완료',
  partial: '일부만 확인됨',
  failed: '확인된 출처 없음',
}

/** 부분 성공·실패·오래된 결과를 구분해 알린다(계획서 §4 Phase 4). */
export default function AnalysisStatus({ brief }: { brief: Intelligence }) {
  const clean = brief.status === 'ready' && brief.needs_review.length === 0
  if (clean && !brief.is_stale) return null

  return (
    <div
      className={`analysis-status analysis-status--${brief.is_stale ? 'stale' : brief.status}`}
      role="status"
    >
      <strong>{brief.is_stale ? '오래된 분석 결과' : STATUS_TEXT[brief.status]}</strong>
      <ul>
        {brief.is_stale && <li>최신성 기준을 지났습니다. 다시 분석하면 최신 출처로 갱신됩니다.</li>}
        {brief.warnings.map((w) => (
          <li key={w}>{w}</li>
        ))}
        {brief.needs_review.map((n) => (
          <li key={n}>확인 필요 · {n}</li>
        ))}
      </ul>
    </div>
  )
}
