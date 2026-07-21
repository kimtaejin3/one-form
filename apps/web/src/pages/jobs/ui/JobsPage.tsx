import { useSuspenseQuery } from '@tanstack/react-query'
import { jobsQuery, JobCard } from '@/entities/job'

export default function JobsPage() {
  const { data } = useSuspenseQuery(jobsQuery)

  return (
    <div className="stack">
      <span className="of-mono">
        내 직무 · {data.role} 기준 맞춤 공고 {data.jobs.length}건
      </span>
      <div className="job-grid">
        {data.jobs.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>
    </div>
  )
}
