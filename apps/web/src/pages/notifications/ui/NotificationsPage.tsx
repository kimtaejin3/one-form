import { useSuspenseQuery } from '@tanstack/react-query'
import { Card } from '@one-form/design-system'
import { NotificationItem, notificationsQuery } from '@/entities/notification'

export default function NotificationsPage() {
  const { data: notifications } = useSuspenseQuery(notificationsQuery)

  return (
    <div className="stack" style={{ maxWidth: 640 }}>
      <strong>전체 알림</strong>
      <Card>
        <div className="notif-list">
          {notifications.map((n) => (
            <NotificationItem key={n.id} notification={n} />
          ))}
        </div>
      </Card>
    </div>
  )
}
