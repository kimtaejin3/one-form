import { useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { ActivityCard, activitiesQuery } from '@/entities/activity'

const CATEGORIES = ['전체', '공모전', '동아리', '대외활동', '교육']

export default function ActivitiesPage() {
  const { data: activities } = useSuspenseQuery(activitiesQuery)
  const [category, setCategory] = useState('전체')

  const shown =
    category === '전체' ? activities : activities.filter((a) => a.category === category)

  return (
    <div className="stack">
      <span className="of-mono">역량 갭 기반 추천 활동 {shown.length}건</span>

      <div className="job-filters">
        {CATEGORIES.map((c) => (
          <button
            key={c}
            type="button"
            className={`filter-chip${category === c ? ' filter-chip--on' : ''}`}
            onClick={() => setCategory(c)}
          >
            {c}
          </button>
        ))}
      </div>

      <div className="job-grid">
        {shown.map((activity) => (
          <ActivityCard key={activity.id} activity={activity} />
        ))}
      </div>
    </div>
  )
}
