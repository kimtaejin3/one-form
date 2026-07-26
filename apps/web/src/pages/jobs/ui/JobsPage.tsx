import { useState } from 'react'
import { Link } from 'react-router-dom'
import { keepPreviousData, useQuery, useSuspenseQuery } from '@tanstack/react-query'
import { Dropdown, Pagination } from '@one-form/design-system'
import { JobCard, jobsQuery } from '@/entities/job'
import { profileQuery } from '@/entities/profile'
import { Loading } from '@/shared/ui'

// 페이지네이션은 매 변경마다 전체를 suspend시키면 UX가 나빠, useSuspenseQuery 대신
// useQuery + keepPreviousData로 이전 목록을 유지한 채 갱신한다.

// 빈 값(= 전체)을 첫 옵션으로 둔 Dropdown 옵션 목록
const opts = (label: string, values: string[]) => [
  { value: '', label: `${label} 전체` },
  ...values.map((v) => ({ value: v, label: v })),
]
const ROLE = opts('직무', ['백엔드', '프론트엔드', '풀스택', '데브옵스', '안드로이드', 'iOS', '데이터', 'ML'])
const EXPERIENCE = opts('경력', ['신입', '경력무관', '1년 이상', '3년 이상', '5년 이상'])
const EMPLOYMENT = opts('고용형태', ['정규직', '계약직', '인턴', '전환형인턴'])
const LOCATION = opts('지역', ['서울', '경기 판교', '부산', '제주', '원격'])

type Filters = { role: string; experience: string; employment: string; location: string }
const EMPTY_FILTERS: Filters = { role: '', experience: '', employment: '', location: '' }

export default function JobsPage() {
  const { data: profile } = useSuspenseQuery(profileQuery)
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)
  const [page, setPage] = useState(1)

  // 채용공고는 마스터 프로필과 대조해 추천하므로, 미등록이면 조회하지 않는다.
  const { data, isFetching } = useQuery({
    ...jobsQuery({ ...filters, page }),
    enabled: profile.registered,
    placeholderData: keepPreviousData,
    throwOnError: true,
  })

  // 필터를 바꾸면 항상 1페이지부터
  function setFilter(key: keyof Filters, value: string) {
    setFilters((f) => ({ ...f, [key]: value }))
    setPage(1)
  }

  if (!profile.registered) {
    return (
      <div className="empty-gate">
        <p>마스터 프로필을 등록하면 내 경험과 맞는 공고를 추천해드려요.</p>
        <Link to="/profile" className="of-btn of-btn--sm">
          마스터 프로필 등록하기
        </Link>
      </div>
    )
  }

  if (!data) return <Loading />

  const totalPages = Math.max(1, Math.ceil(data.total / data.size))

  return (
    <div className="stack">
      <span className="of-mono">
        내 직무 · {data.role} 기준 맞춤 공고 {data.total}건
      </span>

      <div className="job-filters">
        <Dropdown label="직무" value={filters.role} options={ROLE} onChange={(v) => setFilter('role', v)} />
        <Dropdown label="경력" value={filters.experience} options={EXPERIENCE} onChange={(v) => setFilter('experience', v)} />
        <Dropdown label="고용형태" value={filters.employment} options={EMPLOYMENT} onChange={(v) => setFilter('employment', v)} />
        <Dropdown label="지역" value={filters.location} options={LOCATION} onChange={(v) => setFilter('location', v)} />
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

      <Pagination label="공고 목록 페이지" page={data.page} totalPages={totalPages} onChange={setPage} />
    </div>
  )
}
