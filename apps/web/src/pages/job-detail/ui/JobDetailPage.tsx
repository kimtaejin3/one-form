import { Link, useParams } from 'react-router-dom'
import { useSuspenseQuery } from '@tanstack/react-query'
import { JobLogo, SourceBadge, jobDetailQuery } from '@/entities/job'
import { Icon } from '@/shared/ui'

function ListSection({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <section>
      <h3 className="resume-section__title">{title}</h3>
      <ul className="brief-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  )
}

export default function JobDetailPage() {
  const { id = '' } = useParams()
  const { data: job } = useSuspenseQuery(jobDetailQuery(id))
  const { matched_skills, missing_skills } = job.match_analysis

  return (
    <div className="job-detail">
      <Link to="/" className="of-mono job-detail__back">
        ← 공고 목록
      </Link>

      <header className="stack">
        <div className="brief-header">
          <JobLogo company={job.company} domain={job.domain} />
          <div className="job-company">
            <strong>{job.company}</strong>
            <span className="job-cond">{job.conditions}</span>
          </div>
        </div>
        <h2 className="job-detail__title">{job.title}</h2>
        <p className="brief-summary">{job.description}</p>
        <div className="job-foot">
          <span className="job-rate">{job.match_rate}% 매칭</span>
          <span className="job-badge">{job.dday}</span>
          <SourceBadge source={job.source} />
        </div>
        <div className="job-tags">
          {job.tags.map((t) => (
            <span key={t}>#{t}</span>
          ))}
        </div>
      </header>

      <section className="stack">
        <h3 className="resume-section__title">매칭 분석</h3>
        <div className="fit">
          <div className="fit__track">
            <div className="fit__fill" style={{ width: `${job.match_rate}%` }} />
          </div>
          <span className="fit__val">{job.match_rate}%</span>
        </div>
        <p className="job-match">
          <Icon name="spark" size={15} />
          {job.match_reason}
        </p>
        <div className="skill-list">
          {matched_skills.map((s) => (
            <span key={s} className="skill skill--matched">
              ✓ {s}
            </span>
          ))}
          {missing_skills.map((s) => (
            <span key={s} className="skill">
              ○ {s}
            </span>
          ))}
        </div>
      </section>

      <ListSection title="주요 업무" items={job.responsibilities} />
      <ListSection title="자격 요건" items={job.requirements} />
      <ListSection title="우대 사항" items={job.preferred} />

      <section>
        <h3 className="resume-section__title">회사 정보</h3>
        <p className="brief-summary">{job.company_info}</p>
      </section>
    </div>
  )
}
