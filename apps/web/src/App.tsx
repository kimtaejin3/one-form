import { BrowserRouter, Route, Routes } from 'react-router-dom'
import type { ReactElement } from 'react'
import Header from './components/Header'
import AsyncBoundary from './components/AsyncBoundary'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import Companies from './pages/Companies'
import Essays from './pages/Essays'
import Forms from './pages/Forms'
import Activities from './pages/Activities'
import Account from './pages/Account'
import Settings from './pages/Settings'

const ROUTES: { path: string; element: ReactElement }[] = [
  { path: '/', element: <Dashboard /> },
  { path: '/profile', element: <Profile /> },
  { path: '/companies', element: <Companies /> },
  { path: '/essays', element: <Essays /> },
  { path: '/forms', element: <Forms /> },
  { path: '/activities', element: <Activities /> },
  { path: '/account', element: <Account /> },
  { path: '/settings', element: <Settings /> },
]

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <main className="content">
        <Routes>
          {ROUTES.map(({ path, element }) => (
            <Route key={path} path={path} element={<AsyncBoundary>{element}</AsyncBoundary>} />
          ))}
        </Routes>
      </main>
    </BrowserRouter>
  )
}
