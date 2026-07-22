import { useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { JobCard, jobsQuery } from '@/entities/job'
import { FilterSelect, Loading } from '@/shared/ui'

// 페이지네이션은 매 변경마다 전체를 suspend시키면 UX가 나빠, useSuspenseQuery 대신
// useQuery + keepPreviousData로 이전 목록을 유지한 채 갱신한다.
const ROLE = ['백엔드', '프론트엔드', '풀스택', '데브옵스', '안드로이드', 'iOS', '데이터', 'ML']
const EXPERIENCE = ['신입', '경력무관', '1년 이상', '3년 이상', '5년 이상']
const EMPLOYMENT = ['정규직', '계약직', '인턴', '전환형인턴']
const LOCATION = ['서울', '경기 판교', '부산', '제주', '원격']

type Filters = { role: string; experience: string; employment: string; location: string }
const EMPTY_FILTERS: Filters = { role: '', experience: '', employment: '', location: '' }

export default function JobsPage() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)
  const [page, setPage] = useState(1)

  const { data, isFetching } = useQuery({
    ...jobsQuery({ ...filters, page }),
    placeholderData: keepPreviousData,
    throwOnError: true,
  })

  // 필터를 바꾸면 항상 1페이지부터
  function setFilter(key: keyof Filters, value: string) {
    setFilters((f) => ({ ...f, [key]: value }))
    setPage(1)
  }

  if (!data) return <Loading />

  const totalPages = Math.max(1, Math.ceil(data.total / data.size))

  return (
    <div className="stack">
      <span className="of-mono">
        내 직무 · {data.role} 기준 맞춤 공고 {data.total}건
      </span>

      <div className="job-filters">
        <FilterSelect label="직무" value={filters.role} options={ROLE} onChange={(v) => setFilter('role', v)} />
        <FilterSelect label="경력" value={filters.experience} options={EXPERIENCE} onChange={(v) => setFilter('experience', v)} />
        <FilterSelect label="고용형태" value={filters.employment} options={EMPLOYMENT} onChange={(v) => setFilter('employment', v)} />
        <FilterSelect label="지역" value={filters.location} options={LOCATION} onChange={(v) => setFilter('location', v)} />
      </div>

      {data.jobs.length === 0 ? (
        <p className="of-mono">조건에 맞는 공고가 없어요.</p>
      ) : (
        <div className="job-grid" style={{ opacity: isFetching ? 0.55 : 1 }}>
          {data.jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}

      <div className="pagination">
        <button className="of-btn of-btn--sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
          이전
        </button>
        <span className="of-mono">
          {data.page} / {totalPages}
        </span>
        <button
          className="of-btn of-btn--sm"
          disabled={page >= totalPages}
          onClick={() => setPage(page + 1)}
        >
          다음
        </button>
      </div>
    </div>
  )
}
