import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, expect, test, vi } from 'vitest'
import JobsPage from './JobsPage'

function jobFeed() {
  return {
    role: '백엔드 개발',
    total: 100,
    page: 1,
    size: 12,
    jobs: [
      {
        id: 1,
        company: '네이버',
        domain: 'navercorp.com',
        conditions: '신입 · 정규직 · 서울',
        title: '[네이버] 백엔드 개발자',
        tags: ['Java'],
        dday: 'D-3',
        source: '자사 채용',
        match_reason: '잘 맞아요',
      },
    ],
  }
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <JobsPage />
    </QueryClientProvider>,
  )
}

function fetchUrls() {
  return (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.map((c) => String(c[0]))
}

beforeEach(() => {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve(jobFeed()) }),
  ) as unknown as typeof fetch
})

test('직무 필터를 바꾸면 role 파라미터가 인코딩되어 page=1로 다시 요청한다', async () => {
  renderPage()
  await screen.findByText('[네이버] 백엔드 개발자')

  fireEvent.change(screen.getByLabelText('직무'), { target: { value: '백엔드' } })

  await waitFor(() => {
    // 필터 변경 후 요청: role이 URL 인코딩(%EB..)되고 page는 1로 리셋
    expect(fetchUrls().some((u) => u.includes('role=%') && u.includes('page=1'))).toBe(true)
  })
})
