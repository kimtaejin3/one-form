import { render, screen } from '@testing-library/react'
import { Suspense } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, expect, test, vi } from 'vitest'
import JobDetailPage from './JobDetailPage'

function jobDetail() {
  return {
    id: 7,
    company: '토스',
    domain: 'toss.im',
    conditions: '신입 · 정규직 · 서울',
    title: '[토스] 프론트엔드 개발자',
    tags: ['React', 'TypeScript'],
    dday: 'D-5',
    source: '원티드',
    match_rate: 82,
    match_reason: 'React 경험이 요구 스택과 맞아요',
    description: '토스 프론트엔드 챕터에서 함께할 개발자를 찾습니다.',
    responsibilities: ['서비스 화면 개발', 'A/B 테스트 운영'],
    requirements: ['React 실무 경험', 'TypeScript 이해'],
    preferred: ['테스트 코드 작성 경험'],
    company_info: '금융 슈퍼앱을 만드는 회사',
    match_analysis: {
      matched_skills: ['React', 'TypeScript'],
      missing_skills: ['Next.js'],
    },
  }
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/jobs/7']}>
        <Suspense fallback={<div>loading</div>}>
          <Routes>
            <Route path="/jobs/:id" element={<JobDetailPage />} />
          </Routes>
        </Suspense>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve(jobDetail()) }),
  ) as unknown as typeof fetch
})

test('상세 id로 조회해 헤더·매칭 분석·본문 섹션을 렌더한다', async () => {
  renderPage()

  expect(await screen.findByText('[토스] 프론트엔드 개발자')).toBeInTheDocument()
  expect(String((globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0][0])).toContain('/api/jobs/7')

  expect(screen.getByText('82% 매칭')).toBeInTheDocument()
  expect(screen.getByText('React 경험이 요구 스택과 맞아요')).toBeInTheDocument()
  for (const title of ['매칭 분석', '주요 업무', '자격 요건', '우대 사항', '회사 정보']) {
    expect(screen.getByRole('heading', { name: title })).toBeInTheDocument()
  }
  expect(screen.getByText('서비스 화면 개발')).toBeInTheDocument()
})

test('요구 스킬을 충족(✓)·부족(○)으로 구분해 보여준다', async () => {
  renderPage()

  expect(await screen.findByText('✓ React')).toBeInTheDocument()
  expect(screen.getByText('✓ TypeScript')).toBeInTheDocument()
  expect(screen.getByText('○ Next.js')).toBeInTheDocument()
})
