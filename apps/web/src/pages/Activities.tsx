import { Card } from '@one-form/design-system'
import { useApi } from '../useApi'

type Activity = {
  id: number
  name: string
  category: string
  period: string
  fit: number
  fills_gap: string[]
  expected_experience: string
  connections: { company: string; role: string }[]
}

export default function Activities() {
  const activities = useApi<Activity[]>('/activities')

  return (
    <>
      <h2 className="of-h2">활동 추천</h2>
      <p className="page-desc">
        역량 갭 분석을 기반으로 지금 가장 도움이 되는 IT 동아리·대외활동을 추천합니다.
      </p>
      {!activities ? (
        <p className="of-mono">불러오는 중…</p>
      ) : (
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
      )}
    </>
  )
}
