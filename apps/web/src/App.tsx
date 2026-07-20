import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom'
import type { ReactElement } from 'react'
import Header from './components/Header'
import AsyncBoundary from './components/AsyncBoundary'
import Jobs from './pages/Jobs'
import Profile from './pages/Profile'
import Companies from './pages/Companies'
import Essays from './pages/Essays'
import Forms from './pages/Forms'
import Activities from './pages/Activities'
import Account from './pages/Account'
import Settings from './pages/Settings'

const ROUTES: { path: string; element: ReactElement }[] = [
  { path: '/', element: <Jobs /> },
  { path: '/profile', element: <Profile /> },
  { path: '/companies', element: <Companies /> },
  { path: '/essays', element: <Essays /> },
  { path: '/forms', element: <Forms /> },
  { path: '/activities', element: <Activities /> },
  { path: '/account', element: <Account /> },
  { path: '/settings', element: <Settings /> },
]

// 경로가 바뀔 때마다 Routes를 새로 마운트해, 새 페이지가 suspend하면
// 이전 화면을 붙잡지 않고 곧바로 로딩(Suspense fallback)이 보이게 한다.
function AppRoutes() {
  const location = useLocation()
  return (
    <Routes location={location} key={location.pathname}>
      {ROUTES.map(({ path, element }) => (
        <Route key={path} path={path} element={<AsyncBoundary>{element}</AsyncBoundary>} />
      ))}
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <main className="content">
        <AppRoutes />
      </main>
    </BrowserRouter>
  )
}
