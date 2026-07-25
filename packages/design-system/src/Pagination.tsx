export type PaginationProps = {
  /** 1-based 현재 페이지 */
  page: number
  totalPages: number
  onChange: (page: number) => void
  /** 스크린리더용 이름 (한 화면에 페이지네이션이 여럿일 때 구분) */
  label?: string
  className?: string
}

const GAP = '…'

/**
 * 페이지가 많아도 폭이 늘지 않게 첫·끝 페이지와 현재 주변만 남기고 `…`로 접는다.
 * 예: 12페이지 중 5 → 1 … 4 [5] 6 … 12
 */
function items(page: number, totalPages: number): (number | typeof GAP)[] {
  const keep = [...new Set([1, page - 1, page, page + 1, totalPages])]
    .filter((p) => p >= 1 && p <= totalPages)
    .sort((a, b) => a - b)
  return keep.flatMap((p, i) => (i && p - keep[i - 1] > 1 ? [GAP, p] : [p]))
}

/**
 * 목록 페이지 이동. 한 페이지뿐이면 아무것도 그리지 않는다(호출부에서 분기할 일 없게).
 * 현재 페이지는 aria-current="page"로 알리고, 양끝에서 이전/다음은 비활성.
 */
export function Pagination({ page, totalPages, onChange, label, className }: PaginationProps) {
  if (totalPages <= 1) return null

  return (
    <nav
      className={['of-pagination', className].filter(Boolean).join(' ')}
      aria-label={label ?? '페이지'}
    >
      <button
        type="button"
        className="of-pagination__step"
        aria-label="이전 페이지"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
      >
        ‹ 이전
      </button>

      {items(page, totalPages).map((it, i) =>
        it === GAP ? (
          <span key={`gap-${i}`} className="of-pagination__gap" aria-hidden>
            {GAP}
          </span>
        ) : (
          <button
            key={it}
            type="button"
            className={`of-pagination__page${it === page ? ' of-pagination__page--on' : ''}`}
            aria-label={`${it}페이지`}
            aria-current={it === page ? 'page' : undefined}
            onClick={() => onChange(it)}
          >
            {it}
          </button>
        ),
      )}

      <button
        type="button"
        className="of-pagination__step"
        aria-label="다음 페이지"
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
      >
        다음 ›
      </button>
    </nav>
  )
}
