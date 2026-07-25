import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { Suspense } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import EssaysPage from './EssaysPage'

// 문항 풀 + 기업 매핑. 1은 두 회사가 공유(재사용), 4는 어떤 회사도 안 쓰는 공통 문항.
const BASE = [
  {
    id: 1,
    tag: '지원동기',
    prompt: '{회사}에 지원한 이유는?',
    char_limit: 700,
    answer: '',
    status: '미작성',
    companies: [
      { name: '네이버', deadline: '2026-07-28' },
      { name: '토스', deadline: '2026-07-26' },
    ],
  },
  {
    id: 2,
    tag: '경험',
    prompt: '문제를 해결한 경험은?',
    char_limit: 10,
    answer: '토스에 저장해 둔 답변\n둘째 줄',
    status: '초안 완료',
    companies: [{ name: '토스', deadline: '2026-07-26' }],
  },
  {
    id: 3,
    tag: '포부',
    prompt: '입사 후 포부는?',
    char_limit: 500,
    answer: '',
    status: '작성 중',
    companies: [{ name: '네이버', deadline: '2026-07-28' }],
  },
  {
    id: 4,
    tag: '자기소개',
    prompt: '본인을 한 문장으로 소개하면?',
    char_limit: 500,
    answer: '',
    status: '미작성',
    companies: [],
  },
]

// 저장이 GET 결과에 반영되는 서버를 흉내낸다 — 매 응답을 복사해 돌려주지 않으면
// react-query가 같은 객체를 보고 갱신을 건너뛴다.
let store: typeof BASE

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true })
  vi.setSystemTime(new Date('2026-07-25T09:00:00'))
  store = BASE.map((q) => ({ ...q }))
  globalThis.fetch = vi.fn(async (url, init) => {
    const path = String(url)
    if (path.includes('/essays/draft')) {
      return { ok: true, json: async () => ({ question_id: 3, draft: 'AI가 쓴 초안' }) }
    }
    const saved = path.match(/\/essays\/questions\/(\d+)\/answer$/)
    if (saved) {
      const body = JSON.parse(String((init as RequestInit).body))
      const question = store.find((q) => q.id === Number(saved[1]))!
      Object.assign(question, { answer: body.content, status: body.status })
      return { ok: true, json: async () => ({ ...question }) }
    }
    return { ok: true, json: async () => store.map((q) => ({ ...q })) }
  }) as unknown as typeof fetch
})

afterEach(() => vi.useRealTimers())

function fetchCalls() {
  return (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls
}

function items() {
  return screen.getAllByRole('button', { name: /\?/ })
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

function toCompanyView() {
  fireEvent.click(screen.getByRole('tab', { name: '기업별' }))
}

async function pickCompany(name: string) {
  fireEvent.click(screen.getByRole('combobox', { name: '기업 선택' }))
  fireEvent.click(await screen.findByRole('option', { name }))
}

test('문항별 뷰는 문항 풀 전체를 재사용 범위와 함께 보여준다', async () => {
  renderPage()

  await waitFor(() => expect(items()).toHaveLength(4))
  expect(within(item('지원한 이유')).getByText('2개 기업 사용 · 700자')).toBeTruthy()
  expect(within(item('한 문장으로 소개')).getByText('공통 · 500자')).toBeTruthy()
  expect(screen.getByText('진행: 전체 4문항 중 1 완료')).toBeTruthy()
  // 기업 맥락이 없으므로 {회사}는 '귀사'
  expect(item('지원한 이유').textContent).toContain('귀사에 지원한 이유는?')
})

test('기업별 뷰는 그 회사 문항만 보여주고 마감 D-day를 붙인다', async () => {
  renderPage()
  await waitFor(() => expect(items()).toHaveLength(4))

  toCompanyView()
  // 마감 임박순 첫 회사(토스)가 기본 선택 — 토스 문항 2개만
  expect(items()).toHaveLength(2)
  expect(screen.getByText('마감 2026-07-26 · D-1')).toBeTruthy()
  expect(screen.queryByText(/입사 후 포부/)).toBeNull()

  await pickCompany('네이버')
  expect(items()).toHaveLength(2)
  expect(screen.getByText('마감 2026-07-28 · D-3')).toBeTruthy()
  expect(item('입사 후 포부')).toBeTruthy()
  // 기업 맥락이 붙어 {회사}가 회사명으로 치환된다
  expect(item('지원한 이유').textContent).toContain('네이버에 지원한 이유는?')

  // 문항별로 돌아오면 다시 전체 풀
  fireEvent.click(screen.getByRole('tab', { name: '문항별' }))
  expect(items()).toHaveLength(4)
})

test('검색이 문항 텍스트·유형·회사명으로 목록을 좁힌다', async () => {
  renderPage()
  await waitFor(() => expect(items()).toHaveLength(4))
  const box = screen.getByLabelText('문항 검색')

  fireEvent.change(box, { target: { value: '포부' } }) // 유형
  expect(items()).toHaveLength(1)
  expect(item('입사 후 포부')).toBeTruthy()

  fireEvent.change(box, { target: { value: '토스' } }) // 회사명
  expect(items()).toHaveLength(2)

  fireEvent.change(box, { target: { value: '한 문장으로' } }) // 문항 텍스트
  expect(items()).toHaveLength(1)

  fireEvent.change(box, { target: { value: '없는말' } })
  expect(screen.queryAllByRole('button', { name: /\?/ })).toHaveLength(0)
  expect(screen.getByText('해당하는 문항이 없어요.')).toBeTruthy()
})

test('본문은 원본으로 편집하고 미리보기가 현재 맥락으로 치환한다', async () => {
  renderPage()
  const textarea = await screen.findByLabelText('자소서 본문')

  fireEvent.change(textarea, { target: { value: '저는 {회사}의 인재상에 맞습니다.' } })
  // 문항별 = 기업 맥락 없음 → 귀사
  expect(screen.getByLabelText('답변 미리보기').textContent).toBe('저는 귀사의 인재상에 맞습니다.')

  toCompanyView()
  await pickCompany('네이버')
  fireEvent.click(item('지원한 이유'))
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('저는 {회사}의 인재상에 맞습니다.') // 원본 유지
  expect(screen.getByLabelText('답변 미리보기').textContent).toBe('저는 네이버의 인재상에 맞습니다.')
})

test('{회사} 삽입 버튼이 커서 자리에 토큰을 넣는다', async () => {
  renderPage()
  const textarea = (await screen.findByLabelText('자소서 본문')) as HTMLTextAreaElement

  fireEvent.change(textarea, { target: { value: '저는 입니다' } })
  textarea.setSelectionRange(3, 3)
  fireEvent.click(screen.getByRole('button', { name: '{회사} 삽입' }))

  expect(textarea).toHaveValue('저는 {회사}입니다')
  expect(screen.getByLabelText('답변 미리보기').textContent).toBe('저는 귀사입니다')
})

test('저장은 문항 id로 올라가고 미리보기·완료율이 갱신된다', async () => {
  renderPage()
  const textarea = await screen.findByLabelText('자소서 본문')
  expect(screen.getByText('진행: 전체 4문항 중 1 완료')).toBeTruthy()

  fireEvent.change(textarea, { target: { value: '{회사} 답변 첫 줄\n둘째 줄' } })
  fireEvent.click(screen.getByRole('button', { name: '저장' }))

  await waitFor(() => expect(preview('지원한 이유')).toBe('귀사 답변 첫 줄'))
  const [url, init] = fetchCalls().find(([u]) => String(u).includes('/answer'))!
  expect(String(url)).toBe('/api/essays/questions/1/answer')
  expect((init as RequestInit).method).toBe('PUT')
  expect(JSON.parse(String((init as RequestInit).body))).toEqual({
    content: '{회사} 답변 첫 줄\n둘째 줄', // 저장은 원본(토큰 포함)
    status: '작성 중',
  })

  fireEvent.click(screen.getByLabelText('초안 완료'))
  await waitFor(() => expect(screen.getByText('진행: 전체 4문항 중 2 완료')).toBeTruthy())
})

test('본문을 비우고 저장하면 상태가 미작성으로 돌아간다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')
  fireEvent.click(item('문제를 해결한 경험'))
  fireEvent.change(screen.getByLabelText('자소서 본문'), { target: { value: '' } })
  fireEvent.click(screen.getByRole('button', { name: '저장' }))

  await waitFor(() => expect(preview('문제를 해결한 경험')).toBe('미작성'))
  const [, init] = fetchCalls().find(([u]) => String(u).includes('/answer'))!
  expect(JSON.parse(String((init as RequestInit).body)).status).toBe('미작성')
})

// 그냥 [저장]이 사용자가 표시해 둔 "초안 완료"를 말없이 "작성 중"으로 되돌리면 완료율이 깨진다.
test('초안 완료 문항을 다시 저장해도 완료로 남고, 체크를 풀면 작성 중으로 내려간다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')
  fireEvent.click(item('문제를 해결한 경험'))

  fireEvent.change(screen.getByLabelText('자소서 본문'), { target: { value: '고쳐 쓴 답변' } })
  fireEvent.click(screen.getByRole('button', { name: '저장' }))

  await waitFor(() => expect(preview('문제를 해결한 경험')).toBe('고쳐 쓴 답변'))
  const [, init] = fetchCalls().find(([u]) => String(u).includes('/answer'))!
  expect(JSON.parse(String((init as RequestInit).body)).status).toBe('초안 완료')
  expect(screen.getByText('진행: 전체 4문항 중 1 완료')).toBeTruthy()

  fireEvent.click(screen.getByLabelText('초안 완료'))
  await waitFor(() => expect(screen.getByText('진행: 전체 4문항 중 0 완료')).toBeTruthy())
})

test('AI 초안이 textarea에 들어가고 글자 수 초과를 경고한다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')

  fireEvent.click(screen.getByRole('button', { name: 'AI 초안 생성' }))
  await waitFor(() => expect(screen.getByLabelText('자소서 본문')).toHaveValue('AI가 쓴 초안'))
  const [, draftInit] = fetchCalls().find(([u]) => String(u).includes('/draft'))!
  expect(JSON.parse(String((draftInit as RequestInit).body))).toEqual({ question_id: 1 })
  expect(screen.getByText('8 / 700자')).toBeTruthy()

  // char_limit 10인 문항으로 옮기면 초과 경고
  fireEvent.click(item('문제를 해결한 경험'))
  fireEvent.change(screen.getByLabelText('자소서 본문'), {
    target: { value: '열두글자를넘기는본문입니다' },
  })
  expect(screen.getByText(/자 초과/)).toBeTruthy()
})

// 재구조가 만든 데이터 소실 회귀(문항 전환 = 본문 초기화)를 못박는다.
test('문항을 옮겼다 돌아와도 저장 전 본문이 유지된다', async () => {
  renderPage()
  fireEvent.change(await screen.findByLabelText('자소서 본문'), {
    target: { value: '내가 쓴 소중한 본문' },
  })

  fireEvent.click(item('입사 후 포부'))
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('') // 다른 문항은 자기 본문(빈 값)

  fireEvent.click(item('지원한 이유'))
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('내가 쓴 소중한 본문')
})

// jsdom은 confirm을 구현하지 않아 스텁 없이는 이 분기를 못 태운다 — 두 경로 모두 검증.
test('작성 중 본문이 있으면 초안 생성 전에 덮어쓰기를 확인한다', async () => {
  const confirmed = vi.spyOn(window, 'confirm').mockReturnValue(false)
  renderPage()
  fireEvent.change(await screen.findByLabelText('자소서 본문'), {
    target: { value: '내가 쓴 소중한 본문' },
  })

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
  expect(badge('입사 후 포부').textContent).toBe('작성 중')
  expect(badge('입사 후 포부').className).toContain('of-status--doing')
  expect(badge('지원한 이유').className).toContain('of-status--todo')
  expect(badge('문제를 해결한 경험').className).toContain('of-status--done')
})

// mutate 변수로 대상 문항을 넘기는 이유를 못박는다. 응답이 늦게 와도 "지금 보고 있는 문항"이
// 아니라 "요청한 문항"에 들어가야 하며, 어긋나면 남의 본문을 덮어쓰는 조용한 손실이 된다.
test('생성 중 다른 문항으로 옮겨도 초안은 요청한 문항에만 들어간다', async () => {
  let release!: () => void
  const pending = new Promise<void>((r) => (release = r))
  globalThis.fetch = vi.fn(async (url) => {
    if (!String(url).includes('/essays/draft')) return { ok: true, json: async () => store }
    await pending
    return { ok: true, json: async () => ({ question_id: 1, draft: 'AI가 쓴 초안' }) }
  }) as unknown as typeof fetch

  renderPage()
  await screen.findByLabelText('자소서 본문')

  fireEvent.click(screen.getByRole('button', { name: 'AI 초안 생성' })) // 1번 문항에 요청
  fireEvent.click(item('입사 후 포부')) // 응답 전에 이동
  release()

  await waitFor(() => expect(screen.getByLabelText('자소서 본문')).toHaveValue(''))
  fireEvent.click(item('지원한 이유'))
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('AI가 쓴 초안')
})

// 재설계의 핵심 주장: 답변은 기업이 아니라 문항에 붙는다. 한 번 저장한 답변이 그 문항을 묻는
// 모든 기업 뷰에 그대로 나타나고, 회사명만 맥락에 맞게 갈려야 한다.
test('문항에 저장한 답변은 그 문항을 쓰는 모든 기업에서 재사용된다', async () => {
  renderPage()
  const textarea = await screen.findByLabelText('자소서 본문') // 1번(네이버·토스 공유)

  fireEvent.change(textarea, { target: { value: '{회사}에 기여하겠습니다' } })
  fireEvent.click(screen.getByRole('button', { name: '저장' }))
  await waitFor(() => expect(preview('지원한 이유')).toBe('귀사에 기여하겠습니다'))

  // 저장 요청은 회사가 아니라 문항 id로만 나간다 — 기업별 저장이 따로 없다.
  expect(fetchCalls().filter(([u]) => String(u).includes('/answer'))).toHaveLength(1)

  toCompanyView()
  await pickCompany('네이버')
  expect(preview('지원한 이유')).toBe('네이버에 기여하겠습니다')

  await pickCompany('토스')
  expect(preview('지원한 이유')).toBe('토스에 기여하겠습니다')
  // 같은 원본 하나를 재사용한다 — 회사마다 다시 쓰지 않는다.
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('{회사}에 기여하겠습니다')
})

async function pickTag(name: string) {
  fireEvent.click(screen.getByRole('combobox', { name: '유형 필터' }))
  fireEvent.click(await screen.findByRole('option', { name }))
}

// 페이지네이션·필터를 태우려면 한 페이지(8개)를 넘는 풀이 필요하다.
function manyQuestions(n: number) {
  return Array.from({ length: n }, (_, i) => ({
    id: i + 1,
    tag: i % 2 ? '경험' : '역량',
    prompt: `${i + 1}번 문항은?`,
    char_limit: 500,
    answer: '',
    status: '미작성',
    companies: [{ name: '큰회사', deadline: '2026-08-01' }],
  }))
}

test('유형 필터가 문항별 뷰에서만 목록을 좁히고 검색과 함께 걸린다', async () => {
  renderPage()
  await waitFor(() => expect(items()).toHaveLength(4))

  await pickTag('경험')
  expect(items()).toHaveLength(1)
  expect(item('문제를 해결한 경험')).toBeTruthy()

  // 검색과 AND — '경험' 유형 안에서 '포부'를 찾으면 아무것도 없다
  fireEvent.change(screen.getByLabelText('문항 검색'), { target: { value: '포부' } })
  expect(screen.getByText('해당하는 문항이 없어요.')).toBeTruthy()

  fireEvent.change(screen.getByLabelText('문항 검색'), { target: { value: '' } })
  await pickTag('전체 유형')
  expect(items()).toHaveLength(4)

  // 기업별 뷰는 회사 선택이 주 필터라 유형 필터를 두지 않는다
  toCompanyView()
  expect(screen.queryByRole('combobox', { name: '유형 필터' })).toBeNull()
})

test('문항이 한 페이지 이하면 페이지네이션을 감춘다', async () => {
  renderPage()
  await waitFor(() => expect(items()).toHaveLength(4))
  expect(screen.queryByRole('navigation')).toBeNull()
})

test('페이지당 8개로 끊어 보여주고 이동한다', async () => {
  store = manyQuestions(20) as unknown as typeof store
  renderPage()

  await waitFor(() => expect(items()).toHaveLength(8))
  expect(item('1번 문항은?')).toBeTruthy()
  expect(items().some((el) => el.textContent?.includes('9번 문항은?'))).toBe(false)
  expect(screen.getByRole('button', { name: '1페이지' })).toHaveAttribute('aria-current', 'page')

  fireEvent.click(screen.getByRole('button', { name: '다음 페이지' }))
  expect(item('9번 문항은?')).toBeTruthy()
  expect(screen.getByRole('button', { name: '2페이지' })).toHaveAttribute('aria-current', 'page')

  fireEvent.click(screen.getByRole('button', { name: '3페이지' }))
  expect(items()).toHaveLength(4) // 마지막 페이지는 남은 4개
  expect(screen.getByRole('button', { name: '다음 페이지' })).toBeDisabled()

  // 검색이 바뀌면 1페이지로 리셋 — 안 그러면 짧아진 목록에서 빈 화면을 본다
  fireEvent.change(screen.getByLabelText('문항 검색'), { target: { value: '20번 문항' } })
  expect(items()).toHaveLength(1)
  expect(screen.queryByRole('navigation')).toBeNull()

  fireEvent.change(screen.getByLabelText('문항 검색'), { target: { value: '' } })
  expect(screen.getByRole('button', { name: '1페이지' })).toHaveAttribute('aria-current', 'page')
  expect(item('1번 문항은?')).toBeTruthy()
})

test('유형·뷰를 바꿔도 1페이지로 리셋된다', async () => {
  store = manyQuestions(20) as unknown as typeof store
  renderPage()
  await waitFor(() => expect(items()).toHaveLength(8))

  fireEvent.click(screen.getByRole('button', { name: '3페이지' }))
  await pickTag('경험') // 유형 변경 → 1페이지
  expect(screen.getByRole('button', { name: '1페이지' })).toHaveAttribute('aria-current', 'page')
  expect(items()).toHaveLength(8)

  fireEvent.click(screen.getByRole('button', { name: '2페이지' }))
  toCompanyView() // 뷰 변경 → 1페이지 (기업별에도 페이지네이션은 그대로 붙는다)
  expect(screen.getByRole('button', { name: '1페이지' })).toHaveAttribute('aria-current', 'page')
  expect(items()).toHaveLength(8)
})

test('페이지가 많으면 첫·끝과 현재 주변만 남기고 말줄임한다', async () => {
  store = manyQuestions(100) as unknown as typeof store
  renderPage()
  await waitFor(() => expect(items()).toHaveLength(8))

  // 13페이지 중 1 → 1 2 … 13
  expect(screen.getAllByText('…')).toHaveLength(1)
  expect(screen.queryByRole('button', { name: '5페이지' })).toBeNull()

  for (let i = 0; i < 4; i++) fireEvent.click(screen.getByRole('button', { name: '다음 페이지' }))

  // 13페이지 중 5 → 1 … 4 [5] 6 … 13
  expect(screen.getAllByText('…')).toHaveLength(2)
  expect(screen.getByRole('button', { name: '5페이지' })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('button', { name: '13페이지' })).toBeTruthy()
  expect(screen.queryByRole('button', { name: '8페이지' })).toBeNull()
  expect(item('33번 문항은?')).toBeTruthy() // 5페이지 = 33~40
})
