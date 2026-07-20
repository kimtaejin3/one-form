import { useSuspenseQuery } from '@tanstack/react-query'
import { Card } from '@one-form/design-system'
import { applicationsQuery } from '../queries/applications'

const STATUSES = ['작성 중', '지원 완료', '서류 합격', '면접 예정']

export default function Dashboard() {
  const { data: apps } = useSuspenseQuery(applicationsQuery)

  return (
    <div className="kanban">
      {STATUSES.map((status) => {
        const items = apps.filter((a) => a.status === status)
        return (
          <div key={status} className="kanban-col">
            <span className="of-mono">
              {status} · {items.length}
            </span>
            {items.map((a) => (
              <Card key={a.id} className="kanban-card">
                <strong>{a.company}</strong>
                <span className="role">{a.role}</span>
                <span className="of-mono">
                  {a.channel} · ~{a.deadline}
                </span>
              </Card>
            ))}
          </div>
        )
      })}
    </div>
  )
}
