import { useSuspenseQuery } from '@tanstack/react-query'
import { activitiesQuery, ActivityCard } from '@/entities/activity'

export default function ActivitiesPage() {
  const { data: activities } = useSuspenseQuery(activitiesQuery)

  return (
    <div className="stack">
      {activities.map((activity) => (
        <ActivityCard key={activity.id} activity={activity} />
      ))}
    </div>
  )
}
