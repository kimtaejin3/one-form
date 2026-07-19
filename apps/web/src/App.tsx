import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import Companies from './pages/Companies'
import Essays from './pages/Essays'
import Forms from './pages/Forms'
import Activities from './pages/Activities'

const NAV = [
  { to: '/', label: '대시보드' },
  { to: '/profile', label: '마스터 프로필' },
  { to: '/companies', label: '기업 인텔리전스' },
  { to: '/essays', label: '자소서 허브' },
  { to: '/forms', label: '양식 변환' },
  { to: '/activities', label: '활동 추천' },
]

export default function App() {
  return (
    <BrowserRouter>
      <header className="chrome">
        <div className="topbar">
          <span className="logo">
            ONEFORM<span className="logo-dot">.</span>
          </span>
        </div>
        <nav className="tabbar">
          {NAV.map(({ to, label }) => (
            <NavLink key={to} to={to} end={to === '/'}>
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="/essays" element={<Essays />} />
          <Route path="/forms" element={<Forms />} />
          <Route path="/activities" element={<Activities />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
