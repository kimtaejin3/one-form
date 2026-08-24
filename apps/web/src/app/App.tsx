import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom'
import type { ReactElement } from 'react'
import { Header } from '@/widgets/header'
import { AsyncBoundary } from '@/shared/ui'
import { JobsPage } from '@/pages/jobs'
import { JobDetailPage } from '@/pages/job-detail'
import { ProfilePage } from '@/pages/profile'
import { ResumeGalleryPage } from '@/pages/resume-gallery'
import { ResumeBuilderPage } from '@/pages/resume-builder'
import { FormsPage } from '@/pages/forms'
import { AccountPage } from '@/pages/account'
import { SettingsPage } from '@/pages/settings'
import { NotificationsPage } from '@/pages/notifications'
import { HomePage } from '@/pages/home'

const ROUTES: { path: string; element: ReactElement }[] = [
  { path: '/', element: <HomePage /> },
  { path: '/jobs', element: <JobsPage /> },
  { path: '/jobs/:id', element: <JobDetailPage /> },
  { path: '/profile', element: <ProfilePage /> },
  { path: '/resume', element: <ResumeGalleryPage /> },
  { path: '/resume/new', element: <ResumeBuilderPage /> },
  { path: '/resume/edit/:id', element: <ResumeBuilderPage /> },
  { path: '/forms', element: <FormsPage /> },
  { path: '/account', element: <AccountPage /> },
  { path: '/settings', element: <SettingsPage /> },
  { path: '/notifications', element: <NotificationsPage /> },
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
