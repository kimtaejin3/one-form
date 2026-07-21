import { Link, NavLink } from 'react-router-dom'
import { Icon } from '@/shared/ui'
import TabBar from './TabBar'

export default function Header() {
  return (
    <header className="chrome">
      <div className="topbar">
        <Link to="/" className="logo" aria-label="홈으로">
          ONEFORM<span className="logo-dot">.</span>
        </Link>
        <div className="search">
          <Icon name="search" size={18} />
          <input type="search" placeholder="기업·공고 검색" aria-label="기업·공고 검색" />
        </div>
        <div className="topbar-right">
          <button className="icon-btn" type="button" aria-label="알림">
            <Icon name="bell" />
            <span className="dot" />
          </button>
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
