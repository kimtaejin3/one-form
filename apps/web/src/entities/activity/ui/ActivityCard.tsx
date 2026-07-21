import { Icon } from '@/shared/ui'
import type { Activity } from '../model'

export default function ActivityCard({ activity }: { activity: Activity }) {
  return (
    <article className="job-card">
      <div className="activity-head">
        <span className="of-chip">{activity.category}</span>
        <span className="job-cond">{activity.dday}</span>
      </div>
      <h3 className="job-title">{activity.name}</h3>
      <span className="of-mono">
        {activity.organizer} · {activity.period}
      </span>
      <div className="job-tags">
        {activity.fills_gap.map((g) => (
          <span key={g}>#{g}</span>
        ))}
      </div>
      <p className="job-match">
        <Icon name="spark" size={15} />
        {activity.expected_experience}
      </p>
      <div className="job-foot">
        <span className="job-badge">적합도 {activity.fit}%</span>
        {activity.connections[0] && (
          <span className="job-badge">
            {activity.connections[0].company} · {activity.connections[0].role}
          </span>
        )}
      </div>
    </article>
  )
}
