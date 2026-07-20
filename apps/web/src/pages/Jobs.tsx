import { useSuspenseQuery } from '@tanstack/react-query'
import { Icon } from '../components/Icon'
import JobLogo from '../components/JobLogo'
import { jobsQuery } from '../queries/jobs'

export default function Jobs() {
  const { data } = useSuspenseQuery(jobsQuery)

  return (
    <div className="stack">
      <span className="of-mono">
        내 직무 · {data.role} 기준 맞춤 공고 {data.jobs.length}건
      </span>
      <div className="job-grid">
        {data.jobs.map((job) => (
          <article key={job.id} className="job-card">
            <div className="job-head">
              <JobLogo company={job.company} domain={job.domain} />
              <div className="job-company">
                <strong>{job.company}</strong>
                <span className="job-cond">{job.conditions}</span>
              </div>
              <button className="job-bookmark" type="button" aria-label="북마크">
                <Icon name="bookmark" size={20} />
              </button>
            </div>
            <h3 className="job-title">{job.title}</h3>
            <div className="job-tags">
              {job.tags.map((t) => (
                <span key={t}>#{t}</span>
              ))}
            </div>
            <p className="job-match">
              <Icon name="spark" size={15} />
              {job.match_reason}
            </p>
            <div className="job-foot">
              <span className="job-badge">{job.dday}</span>
              <span className="job-badge">{job.source}</span>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
