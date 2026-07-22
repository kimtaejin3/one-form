import { Suspense, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useSuspenseQuery } from '@tanstack/react-query'
import { Icon } from '@/shared/ui'
import { NotificationItem, notificationsQuery } from '@/entities/notification'

export default function NotificationBell() {
  const [open, setOpen] = useState(false)

  return (
    <div className="notif">
      <button
        className="icon-btn"
        type="button"
        aria-label="알림"
        onClick={() => setOpen((v) => !v)}
      >
        <Icon name="bell" />
        <span className="dot" />
      </button>

      {open && (
        <>
          <div className="popover-backdrop" onClick={() => setOpen(false)} />
          <div className="notif-popover">
            <div className="notif-popover__head">
              <strong>알림</strong>
            </div>
            <Suspense
              fallback={<div className="notif-popover__loading of-mono">불러오는 중…</div>}
            >
              <PopoverList />
            </Suspense>
            <NavLink to="/notifications" className="notif-popover__all" onClick={() => setOpen(false)}>
              전체 알림 보기
            </NavLink>
          </div>
        </>
      )}
    </div>
  )
}

function PopoverList() {
  const { data } = useSuspenseQuery(notificationsQuery)
  return (
    <div className="notif-list">
      {data.slice(0, 5).map((n) => (
        <NotificationItem key={n.id} notification={n} />
      ))}
    </div>
  )
}
