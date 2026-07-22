import type { Notification } from '../model'

export default function NotificationItem({ notification }: { notification: Notification }) {
  return (
    <div className={`notif-item${notification.unread ? ' notif-item--unread' : ''}`}>
      <div className="notif-item__top">
        <span className="of-chip">{notification.type}</span>
        <strong className="notif-item__title">{notification.title}</strong>
        {notification.unread && <span className="notif-item__dot" />}
      </div>
      <span className="notif-item__msg">{notification.message}</span>
      <span className="notif-item__time">{notification.time}</span>
    </div>
  )
}
