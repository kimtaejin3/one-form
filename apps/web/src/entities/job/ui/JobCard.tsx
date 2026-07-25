import { Icon } from '@/shared/ui'
import type { Job } from '../model'
import JobLogo from './JobLogo'
import SourceBadge from './SourceBadge'

export default function JobCard({ job }: { job: Job }) {
  return (
    <article className="job-card">
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
        <SourceBadge source={job.source} />
      </div>
    </article>
  )
}
