import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Suspense } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, expect, test, vi } from 'vitest'
import EssaysPage from './EssaysPage'

const ESSAYS = [
  { id: 1, company: '네이버', tag: '경험', question: '네이버 문항 늦은 마감', char_limit: 10, deadline: '2026-08-01', status: '미작성' },
  { id: 2, company: '토스', tag: '역량', question: '토스 문항', char_limit: 1000, deadline: '2026-07-30', status: '초안 완료' },
  { id: 3, company: '네이버', tag: '포부', question: '네이버 문항 이른 마감', char_limit: 500, deadline: '2026-07-26', status: '작성 중' },
]

beforeEach(() => {
  globalThis.fetch = vi.fn((url) => {
    const body = String(url).includes('/essays/draft')
      ? { essay_id: 1, draft: 'AI가 쓴 초안' }
      : ESSAYS
    return Promise.resolve({ ok: true, json: () => Promise.resolve(body) })
  }) as unknown as typeof fetch
})

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <Suspense fallback={<div>loading</div>}>
        <EssaysPage />
      </Suspense>
    </QueryClientProvider>,
  )
}

test('회사를 바꾸면 그 회사 문항만 마감 임박순으로 보이고 첫 문항이 선택된다', async () => {
  renderPage()

  // 첫 회사(네이버)의 문항만 노출 + 마감 임박순
  const items = await screen.findAllByRole('button', { name: /네이버 문항/ })
  expect(items.map((el) => el.textContent?.includes('이른 마감'))).toEqual([true, false])
  expect(screen.queryByText('토스 문항')).toBeNull()
  // 선택된 문항의 질문 전문이 작성 패널에 뜬다 (목록 + 패널 = 2곳)
  expect(screen.getAllByText('네이버 문항 이른 마감')).toHaveLength(2)

  fireEvent.click(screen.getByRole('tab', { name: '토스' }))
  expect(screen.getAllByText('토스 문항')).toHaveLength(2)
  expect(screen.queryByText(/네이버 문항/)).toBeNull()
})

test('AI 초안이 textarea에 들어가고 글자 수 초과를 경고한다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')

  fireEvent.click(screen.getByRole('button', { name: 'AI 초안 생성' }))
  await waitFor(() => expect(screen.getByLabelText('자소서 본문')).toHaveValue('AI가 쓴 초안'))

  // 선택된 문항(char_limit 500)은 여유, 10자 제한 문항으로 옮기면 초과 경고
  expect(screen.getByText('8 / 500자')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: /늦은 마감/ }))
  fireEvent.change(screen.getByLabelText('자소서 본문'), { target: { value: '열두글자를넘기는본문입니다' } })
  expect(screen.getByText(/자 초과/)).toBeTruthy()
})

// status → 클래스 매핑은 미지의 값을 조용히 'todo'로 흘려보낸다. 백엔드가 문구를 바꾸면
// 화면상 구분만 사라지고 아무것도 깨지지 않으므로 세 값 모두 못박아 둔다.
test('status마다 다른 배지 클래스로 시각 구분된다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')

  expect(screen.getByText('작성 중').className).toContain('of-status--doing')
  expect(screen.getByText('미작성').className).toContain('of-status--todo')

  fireEvent.click(screen.getByRole('tab', { name: '토스' }))
  expect(screen.getByText('초안 완료').className).toContain('of-status--done')
})
