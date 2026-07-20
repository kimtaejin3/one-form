import { NavLink } from 'react-router-dom'
import { Icon, type IconName } from './Icon'

const NAV: { to: string; label: string; icon: IconName }[] = [
  { to: '/', label: '대시보드', icon: 'dashboard' },
  { to: '/profile', label: '마스터 프로필', icon: 'person' },
  { to: '/companies', label: '기업 인텔리전스', icon: 'business' },
  { to: '/essays', label: '자소서 허브', icon: 'description' },
  { to: '/forms', label: '양식 변환', icon: 'transform' },
  { to: '/activities', label: '활동 추천', icon: 'explore' },
]

export default function TabBar() {
  return (
    <nav className="tabbar">
      {NAV.map(({ to, label, icon }) => (
        <NavLink key={to} to={to} end={to === '/'}>
          <span className="tab-icon">
            <Icon name={icon} size={18} />
          </span>
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
