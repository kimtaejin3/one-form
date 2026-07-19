import { Card } from '@one-form/design-system'
import { useApi } from '../useApi'

type Application = {
  id: number
  company: string
  role: string
  channel: string
  status: string
  deadline: string
}

const STATUSES = ['작성 중', '지원 완료', '서류 합격', '면접 예정']

export default function Dashboard() {
  const apps = useApi<Application[]>('/applications')

  return (
    <>
      <h2 className="of-h2">지원 현황</h2>
      <p className="page-desc">전 채널 지원 상태를 칸반으로 한눈에 트래킹합니다.</p>
      {!apps ? (
        <p className="of-mono">불러오는 중…</p>
      ) : (
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
      )}
    </>
  )
}
