import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { Suspense } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, expect, test, vi } from 'vitest'
import EssaysPage from './EssaysPage'

const BASE = [
  { id: 1, company: '네이버', tag: '경험', question: '네이버 문항 늦은 마감', char_limit: 10, deadline: '2026-08-01', status: '미작성', answer: '' },
  { id: 2, company: '토스', tag: '역량', question: '토스 문항', char_limit: 1000, deadline: '2026-07-30', status: '초안 완료', answer: '토스에 저장해 둔 답변\n둘째 줄' },
  { id: 3, company: '네이버', tag: '포부', question: '네이버 문항 이른 마감', char_limit: 500, deadline: '2026-07-26', status: '작성 중', answer: '' },
]

// 저장이 GET 결과에 반영되는 서버를 흉내낸다 — 매 응답을 복사해 돌려주지 않으면
// react-query가 같은 객체를 보고 갱신을 건너뛴다.
let store: typeof BASE

beforeEach(() => {
  store = BASE.map((e) => ({ ...e }))
  globalThis.fetch = vi.fn(async (url, init) => {
    const path = String(url)
    if (path.includes('/essays/draft')) {
      return { ok: true, json: async () => ({ essay_id: 3, draft: 'AI가 쓴 초안' }) }
    }
    const saved = path.match(/\/essays\/(\d+)\/answer$/)
    if (saved) {
      const body = JSON.parse(String((init as RequestInit).body))
      const essay = store.find((e) => e.id === Number(saved[1]))!
      Object.assign(essay, { answer: body.content, status: body.status })
      return { ok: true, json: async () => ({ ...essay }) }
    }
    return { ok: true, json: async () => store.map((e) => ({ ...e })) }
  }) as unknown as typeof fetch
})

function fetchCalls() {
  return (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls
}

function items() {
  return screen.getAllByRole('button', { name: /문항/ })
}

function item(label: string) {
  const found = items().find((el) => el.textContent?.includes(label))
  if (!found) throw new Error(`문항 없음: ${label}`)
  return found
}

function preview(label: string) {
  return item(label).querySelector('.of-essay-item__preview')?.textContent
}

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

test('기본은 전체 문항이 마감 임박순으로 보이고, 회사 필터로 좁힌다', async () => {
  renderPage()

  // 회사 무관 전체 목록 — 마감 임박순
  await waitFor(() => expect(items()).toHaveLength(3))
  expect(items().map((el) => el.querySelector('.of-essay-item__q')?.textContent)).toEqual([
    '네이버 문항 이른 마감',
    '토스 문항',
    '네이버 문항 늦은 마감',
  ])
  expect(screen.getByRole('tab', { name: '전체' })).toHaveAttribute('aria-selected', 'true')
  // 각 행에 회사·문항유형이 붙는다
  expect(within(item('토스 문항')).getByText('토스 · 역량')).toBeTruthy()

  fireEvent.click(screen.getByRole('tab', { name: '네이버' }))
  expect(items()).toHaveLength(2)
  expect(screen.queryByText('토스 문항')).toBeNull()

  fireEvent.click(screen.getByRole('tab', { name: '전체' }))
  expect(items()).toHaveLength(3)
})

test('문항을 선택하면 저장된 답변이 에디터에 로드되고 리스트엔 첫 줄만 미리보기된다', async () => {
  renderPage()
  // 답변 없는 문항(이른 마감)이 기본 선택 — 미리보기는 "미작성"
  expect(await screen.findByLabelText('자소서 본문')).toHaveValue('')
  expect(preview('이른 마감')).toBe('미작성')

  fireEvent.click(item('토스 문항'))
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('토스에 저장해 둔 답변\n둘째 줄')
  expect(preview('토스 문항')).toBe('토스에 저장해 둔 답변')
})

test('저장하면 PUT으로 답변이 올라가고 미리보기·완료율이 갱신된다', async () => {
  renderPage()
  const textarea = await screen.findByLabelText('자소서 본문')
  expect(screen.getByText('진행: 3개 중 1 완료')).toBeTruthy()

  fireEvent.change(textarea, { target: { value: '저장할 답변 첫 줄\n둘째 줄' } })
  fireEvent.click(screen.getByRole('button', { name: '저장' }))

  await waitFor(() => expect(preview('이른 마감')).toBe('저장할 답변 첫 줄'))
  const [url, init] = fetchCalls().find(([u]) => String(u).includes('/answer'))!
  expect(String(url)).toBe('/api/essays/3/answer')
  expect((init as RequestInit).method).toBe('PUT')
  expect(JSON.parse(String((init as RequestInit).body))).toEqual({
    content: '저장할 답변 첫 줄\n둘째 줄',
    status: '작성 중',
  })

  // 사용자가 "초안 완료"로 표시 → 완료 수도 서버 값으로 다시 그려진다
  fireEvent.click(screen.getByLabelText('초안 완료'))
  await waitFor(() => expect(screen.getByText('진행: 3개 중 2 완료')).toBeTruthy())
})

test('본문을 비우고 저장하면 상태가 미작성으로 돌아간다', async () => {
  renderPage()
  fireEvent.click(await screen.findByRole('tab', { name: '토스' }))
  fireEvent.change(screen.getByLabelText('자소서 본문'), { target: { value: '' } })
  fireEvent.click(screen.getByRole('button', { name: '저장' }))

  await waitFor(() => expect(preview('토스 문항')).toBe('미작성'))
  const [, init] = fetchCalls().find(([u]) => String(u).includes('/answer'))!
  expect(JSON.parse(String((init as RequestInit).body)).status).toBe('미작성')
})

test('AI 초안이 textarea에 들어가고 글자 수 초과를 경고한다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')

  fireEvent.click(screen.getByRole('button', { name: 'AI 초안 생성' }))
  await waitFor(() => expect(screen.getByLabelText('자소서 본문')).toHaveValue('AI가 쓴 초안'))

  // 선택된 문항(char_limit 500)은 여유, 10자 제한 문항으로 옮기면 초과 경고
  expect(screen.getByText('8 / 500자')).toBeTruthy()
  fireEvent.click(item('늦은 마감'))
  fireEvent.change(screen.getByLabelText('자소서 본문'), { target: { value: '열두글자를넘기는본문입니다' } })
  expect(screen.getByText(/자 초과/)).toBeTruthy()
})

test('회사 필터 탭은 ←/→로 이동하고 양끝에서 순환한다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')
  const tablist = screen.getByRole('tablist')

  fireEvent.keyDown(tablist, { key: 'ArrowRight' })
  expect(screen.getByRole('tab', { name: '네이버' })).toHaveAttribute('aria-selected', 'true')
  expect(screen.getByRole('tab', { name: '네이버' })).toHaveFocus()

  // 마지막 탭에서 오른쪽 → 첫 탭으로 순환
  fireEvent.keyDown(tablist, { key: 'ArrowRight' })
  expect(screen.getByRole('tab', { name: '토스' })).toHaveAttribute('aria-selected', 'true')
  fireEvent.keyDown(tablist, { key: 'ArrowRight' })
  expect(screen.getByRole('tab', { name: '전체' })).toHaveAttribute('aria-selected', 'true')
  fireEvent.keyDown(tablist, { key: 'ArrowLeft' })
  expect(screen.getByRole('tab', { name: '토스' })).toHaveAttribute('aria-selected', 'true')
})

// 재구조가 만든 데이터 소실 회귀(문항 전환 = 본문 초기화)를 못박는다.
test('문항을 옮겼다 돌아와도 저장 전 본문이 유지된다', async () => {
  renderPage()
  fireEvent.change(await screen.findByLabelText('자소서 본문'), {
    target: { value: '내가 쓴 소중한 본문' },
  })

  fireEvent.click(item('늦은 마감'))
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('') // 다른 문항은 자기 본문(빈 값)

  fireEvent.click(item('이른 마감'))
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('내가 쓴 소중한 본문')
})

// jsdom은 confirm을 구현하지 않아 스텁 없이는 이 분기를 못 태운다 — 두 경로 모두 검증.
test('작성 중 본문이 있으면 초안 생성 전에 덮어쓰기를 확인한다', async () => {
  const confirmed = vi.spyOn(window, 'confirm').mockReturnValue(false)
  renderPage()
  fireEvent.change(await screen.findByLabelText('자소서 본문'), {
    target: { value: '내가 쓴 소중한 본문' },
  })

  // 취소하면 요청도 안 나가고 본문도 그대로
  fireEvent.click(screen.getByRole('button', { name: 'AI 초안 다시 생성' }))
  expect(confirmed).toHaveBeenCalled()
  expect(fetchCalls().some(([u]) => String(u).includes('/essays/draft'))).toBe(false)
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('내가 쓴 소중한 본문')

  confirmed.mockReturnValue(true)
  fireEvent.click(screen.getByRole('button', { name: 'AI 초안 다시 생성' }))
  await waitFor(() => expect(screen.getByLabelText('자소서 본문')).toHaveValue('AI가 쓴 초안'))
  confirmed.mockRestore()
})

// status → 클래스 매핑은 미지의 값을 조용히 'todo'로 흘려보낸다. 백엔드가 문구를 바꾸면
// 화면상 구분만 사라지고 아무것도 깨지지 않으므로 세 값 모두 못박아 둔다.
test('status마다 다른 배지 클래스로 시각 구분된다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')

  const badge = (label: string) => item(label).querySelector('.of-status')!
  expect(badge('이른 마감').textContent).toBe('작성 중')
  expect(badge('이른 마감').className).toContain('of-status--doing')
  expect(badge('늦은 마감').className).toContain('of-status--todo')
  expect(badge('토스 문항').className).toContain('of-status--done')
})

// mutate 변수로 대상 문항을 넘기는 이유를 못박는다. 응답이 늦게 와도 "지금 보고 있는 문항"이
// 아니라 "요청한 문항"에 들어가야 하며, 어긋나면 남의 본문을 덮어쓰는 조용한 손실이 된다.
test('생성 중 다른 문항으로 옮겨도 초안은 요청한 문항에만 들어간다', async () => {
  let release!: () => void
  const pending = new Promise<void>((r) => (release = r))
  globalThis.fetch = vi.fn(async (url) => {
    if (!String(url).includes('/essays/draft')) return { ok: true, json: async () => store }
    await pending
    return { ok: true, json: async () => ({ essay_id: 3, draft: 'AI가 쓴 초안' }) }
  }) as unknown as typeof fetch

  renderPage()
  await screen.findByLabelText('자소서 본문')

  fireEvent.click(screen.getByRole('button', { name: 'AI 초안 생성' })) // 이른 마감에 요청
  fireEvent.click(item('늦은 마감')) // 응답 전에 이동
  release()

  await waitFor(() => expect(screen.getByLabelText('자소서 본문')).toHaveValue(''))
  fireEvent.click(item('이른 마감'))
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('AI가 쓴 초안')
})
