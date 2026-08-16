import { fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Suspense } from 'react'
import { expect, test, vi } from 'vitest'
import type { ProfileData } from '@/entities/profile'
import ProfilePage from './ProfilePage'

const profile: ProfileData = {
  registered: true,
  personal: {
    photo: '',
    name: '김태진',
    name_en: 'Kim Taejin',
    name_cn: '金泰辰',
    headline: 'Node.js 기반 풀스택 개발자',
    summary: '사용자 문제를 빠르게 해결합니다.',
    address: '서울시',
    phone: '010-1234-5678',
    email: 'taejin@example.com',
    emergency_phone: '010-9876-5432',
    emergency_relation: '부',
  },
  links: [{ label: 'GitHub', url: 'https://github.com/taejin' }],
  educations: [{ school: '한국대학교', major: '컴퓨터공학', period: '2015.03 - 2019.02', status: '졸업', gpa: '4.0' }],
  languages: [{ language: '영어', test: 'TOEIC', score: '900', date: '2020.01' }],
  awards: [{ title: '우수상', org: '한국대학교', date: '2018.12' }],
  certificates: [{ name: '정보처리기사', issuer: '한국산업인력공단', date: '2019.05' }],
  careers: [{ company: '원폼', role: '개발자', period: '2020.01 - 현재', highlights: ['서비스 개발'], stack: ['React'] }],
  projects: [{ name: 'csms_sim3d', organization: '라인월드', role: '개발자', period: '2024.01 - 2024.12', summary: '시뮬레이터', highlights: ['성능 개선'], stack: ['Node.js'] }],
  activities: [{ type: '교육', title: '프론트엔드 교육', org: '원폼', period: '2020.01', description: 'React 교육' }],
  skill_groups: [{ category: '백엔드', skills: ['TypeScript', 'Node.js'] }],
  open_source_contributions: [{ repository: 'nodejs/node', url: 'https://github.com/nodejs/node', highlights: ['문서 개선'] }],
}

function renderPage() {
  globalThis.fetch = vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve(profile) })) as unknown as typeof fetch
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={<div>loading</div>}>
        <ProfilePage />
      </Suspense>
    </QueryClientProvider>,
  )
}

test('확장 프로필 항목을 표시하고 편집할 수 있다', async () => {
  renderPage()

  expect(await screen.findByText('Node.js 기반 풀스택 개발자')).toBeTruthy()
  expect(screen.getByText('TypeScript')).toBeTruthy()
  expect(screen.getByText('nodejs/node')).toBeTruthy()
  expect(screen.getByText('csms_sim3d')).toBeTruthy()
  expect(screen.getByText('라인월드 · 개발자 · 2024.01 - 2024.12')).toBeTruthy()

  fireEvent.click(screen.getByRole('button', { name: '프로필 편집' }))

  expect(screen.getByLabelText('직무 제목')).toHaveValue('Node.js 기반 풀스택 개발자')
  expect(screen.getByText('오픈소스 기여 추가')).toBeTruthy()
})
