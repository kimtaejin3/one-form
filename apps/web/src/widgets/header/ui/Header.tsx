import { Link, NavLink } from 'react-router-dom'
import { Icon, ThemeToggle } from '@/shared/ui'
import TabBar from './TabBar'
import NotificationBell from './NotificationBell'

export default function Header() {
  return (
    <header className="chrome">
      <div className="topbar">
        <Link to="/" className="logo" aria-label="홈으로">
          ONEFORM<span className="logo-dot">.</span>
        </Link>
        <div className="topbar-right">
          <ThemeToggle />
          <NotificationBell />
          <NavLink to="/settings" className="icon-btn" title="설정">
            <Icon name="settings" />
          </NavLink>
          <NavLink to="/account" className="avatar" title="내 프로필">
            <Icon name="person" />
          </NavLink>
        </div>
      </div>
      <TabBar />
    </header>
  )
}
