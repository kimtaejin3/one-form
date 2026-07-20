import { useSuspenseQuery } from '@tanstack/react-query'
import { Card } from '@one-form/design-system'
import { activitiesQuery } from '../queries/activities'

export default function Activities() {
  const { data: activities } = useSuspenseQuery(activitiesQuery)

  return (
    <div className="stack">
      {activities.map((act) => (
        <Card key={act.id}>
          <div className="stack">
            <div className="row">
              <strong>{act.name}</strong>
              <span className="of-chip">{act.category}</span>
              <span className="of-mono">
                {act.period} · 적합도 {act.fit}%
              </span>
            </div>
            <div className="row">
              <span className="of-mono">보완 역량</span>
              {act.fills_gap.map((g) => (
                <span key={g} className="of-chip">
                  {g}
                </span>
              ))}
            </div>
            <span>
              <b>이 활동으로 쓸 경험</b> — {act.expected_experience}
            </span>
            <div className="row">
              <span className="of-mono">연결 가능</span>
              {act.connections.map((c) => (
                <span key={c.company + c.role} className="of-chip">
                  {c.company} · {c.role}
                </span>
              ))}
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}
