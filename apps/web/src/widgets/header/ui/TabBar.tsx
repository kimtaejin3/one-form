import { NavLink } from 'react-router-dom'
import { Icon, type IconName } from '@/shared/ui'

const NAV: { to: string; label: string; icon: IconName }[] = [
  { to: '/', label: '채용공고', icon: 'work' },
  { to: '/profile', label: '마스터 프로필', icon: 'person' },
  { to: '/resume', label: '이력서 빌더', icon: 'description' },
  { to: '/portfolio', label: '포트폴리오 빌더', icon: 'description' },
  { to: '/companies', label: '기업 인텔리전스', icon: 'business' },
  { to: '/essays', label: '자소서 허브', icon: 'description' },
  { to: '/forms', label: '양식 변환', icon: 'transform' },
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
