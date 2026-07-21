import { Card } from '@one-form/design-system'
import type { Activity } from '../model'

export default function ActivityCard({ activity }: { activity: Activity }) {
  return (
    <Card>
      <div className="stack">
        <div className="row">
          <strong>{activity.name}</strong>
          <span className="of-chip">{activity.category}</span>
          <span className="of-mono">
            {activity.period} · 적합도 {activity.fit}%
          </span>
        </div>
        <div className="row">
          <span className="of-mono">보완 역량</span>
          {activity.fills_gap.map((g) => (
            <span key={g} className="of-chip">
              {g}
            </span>
          ))}
        </div>
        <span>
          <b>이 활동으로 쓸 경험</b> — {activity.expected_experience}
        </span>
        <div className="row">
          <span className="of-mono">연결 가능</span>
          {activity.connections.map((c) => (
            <span key={c.company + c.role} className="of-chip">
              {c.company} · {c.role}
            </span>
          ))}
        </div>
      </div>
    </Card>
  )
}
