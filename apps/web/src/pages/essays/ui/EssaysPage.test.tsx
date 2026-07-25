import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { Suspense } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import EssaysPage from './EssaysPage'

// 문항 풀 + (기업 × 문항) 슬롯. 1번은 두 기업이 같은 문항을 묻지만 답변은 슬롯마다 별개다.
// 4번은 어떤 기업도 안 쓰는 문항 → 공통 슬롯 1개.
const BASE = [
  {
    id: 1,
    tag: '지원동기',
    prompt: '지원한 이유는?',
    char_limit: 700,
    slots: [
      { company: '네이버', deadline: '2026-07-28', content: '', status: '미작성' },
      { company: '토스', deadline: '2026-07-26', content: '', status: '미작성' },
    ],
  },
  {
    id: 2,
    tag: '경험',
    prompt: '문제를 해결한 경험은?',
    char_limit: 10,
    slots: [
      {
        company: '토스',
        deadline: '2026-07-26',
        content: '토스에 저장해 둔 답변\n둘째 줄',
        status: '초안 완료',
      },
    ],
  },
  {
    id: 3,
    tag: '포부',
    prompt: '입사 후 포부는?',
    char_limit: 500,
    slots: [{ company: '네이버', deadline: '2026-07-28', content: '', status: '작성 중' }],
  },
  {
    id: 4,
    tag: '자기소개',
    prompt: '본인을 한 문장으로 소개하면?',
    char_limit: 500,
    slots: [{ company: '공통', deadline: '', content: '', status: '미작성' }],
  },
]

// 저장이 GET 결과에 반영되는 서버를 흉내낸다 — 슬롯까지 깊게 복사해 돌려주지 않으면
// react-query가 같은 객체를 보고 갱신을 건너뛴다.
let store: typeof BASE

const copy = (list: typeof BASE) => list.map((q) => ({ ...q, slots: q.slots.map((s) => ({ ...s })) }))

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true })
  vi.setSystemTime(new Date('2026-07-25T09:00:00'))
  store = copy(BASE)
  globalThis.fetch = vi.fn(async (url, init) => {
    const path = String(url)
    if (path.includes('/essays/draft')) {
      return { ok: true, json: async () => ({ question_id: 3, draft: 'AI가 쓴 초안' }) }
    }
    const saved = path.match(/\/essays\/questions\/(\d+)\/answer$/)
    if (saved) {
      const body = JSON.parse(String((init as RequestInit).body))
      const question = store.find((q) => q.id === Number(saved[1]))!
      // 저장은 (기업, 문항) 슬롯 하나만 건드린다.
      const slot = question.slots.find((s) => s.company === body.company)!
      Object.assign(slot, { content: body.content, status: body.status })
      return { ok: true, json: async () => copy([question])[0] }
    }
    return { ok: true, json: async () => copy(store) }
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

function savedBodies() {
  return fetchCalls()
    .filter(([u]) => String(u).includes('/answer'))
    .map(([u, init]) => ({
      url: String(u),
      ...JSON.parse(String((init as RequestInit).body)),
    }))
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

async function pick(label: string, option: string) {
  fireEvent.click(screen.getByRole('combobox', { name: label }))
  fireEvent.click(await screen.findByRole('option', { name: option }))
}

test('문항별 뷰는 문항 풀을 기업 수·작성 집계와 함께 보여준다', async () => {
  renderPage()

  await waitFor(() => expect(items()).toHaveLength(4))
  expect(within(item('지원한 이유')).getByText('2개 기업 · 700자')).toBeTruthy()
  expect(within(item('지원한 이유')).getByText('0/2 기업 작성')).toBeTruthy()
  expect(within(item('입사 후 포부')).getByText('1/1 기업 작성')).toBeTruthy()
  expect(within(item('한 문장으로 소개')).getByText('공통 · 500자')).toBeTruthy()
  // 진행은 문항이 아니라 (기업 × 문항) 슬롯 기준 — 총 5개 중 초안 완료 1개
  expect(screen.getByText('진행: 기업별 문항 5개 중 1 완료')).toBeTruthy()
})

test('문항별 뷰에서 기업을 고르고 작성하면 그 슬롯으로 저장된다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')

  // 기본은 첫 기업 슬롯(네이버)
  expect(screen.getByRole('combobox', { name: '작성할 기업' }).textContent).toContain('네이버')

  await pick('작성할 기업', '토스')
  fireEvent.change(screen.getByLabelText('자소서 본문'), { target: { value: '토스에 낼 답변' } })
  fireEvent.click(screen.getByRole('button', { name: '저장' }))

  await waitFor(() => expect(savedBodies()).toHaveLength(1))
  expect(savedBodies()[0]).toEqual({
    url: '/api/essays/questions/1/answer',
    company: '토스',
    content: '토스에 낼 답변',
    status: '작성 중',
  })
  expect((fetchCalls().find(([u]) => String(u).includes('/answer'))![1] as RequestInit).method).toBe(
    'PUT',
  )

  // 같은 문항의 네이버 슬롯은 그대로 비어 있다 — 답변은 재사용되지 않는다.
  await pick('작성할 기업', '네이버')
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('')
  await waitFor(() => expect(within(item('지원한 이유')).getByText('1/2 기업 작성')).toBeTruthy())
})

test('기업별 뷰는 그 회사 문항·슬롯만 편집한다', async () => {
  renderPage()
  await waitFor(() => expect(items()).toHaveLength(4))

  toCompanyView()
  // 마감 임박순 첫 회사(토스)가 기본 — 토스 문항 2개, 그 회사 슬롯 상태·미리보기
  expect(items()).toHaveLength(2)
  expect(screen.getByText('마감 2026-07-26 · D-1')).toBeTruthy()
  expect(preview('문제를 해결한 경험')).toBe('토스에 저장해 둔 답변')
  expect(within(item('문제를 해결한 경험')).getByText('초안 완료')).toBeTruthy()

  // 기업이 고정이라 에디터엔 기업 선택 드롭다운이 없다
  fireEvent.click(item('지원한 이유'))
  expect(screen.queryByRole('combobox', { name: '작성할 기업' })).toBeNull()
  expect(within(screen.getByLabelText('자소서 본문').closest('.of-essay-panel')!).getByText('토스'))

  fireEvent.change(screen.getByLabelText('자소서 본문'), { target: { value: '토스용 지원동기' } })
  fireEvent.click(screen.getByRole('button', { name: '저장' }))
  await waitFor(() => expect(savedBodies()[0].company).toBe('토스'))

  await pick('기업 선택', '네이버')
  expect(items()).toHaveLength(2)
  expect(screen.getByText('마감 2026-07-28 · D-3')).toBeTruthy()
  // 같은 문항이어도 네이버 슬롯은 미작성 그대로
  expect(preview('지원한 이유')).toBe('미작성')
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('')
})

test('진행 요약과 상태는 슬롯 단위로 갱신된다', async () => {
  renderPage()
  const textarea = await screen.findByLabelText('자소서 본문')
  expect(screen.getByText('진행: 기업별 문항 5개 중 1 완료')).toBeTruthy()

  fireEvent.change(textarea, { target: { value: '네이버에 낼 답변' } })
  fireEvent.click(screen.getByLabelText('초안 완료'))

  await waitFor(() => expect(screen.getByText('진행: 기업별 문항 5개 중 2 완료')).toBeTruthy())
  expect(savedBodies()[0]).toMatchObject({ company: '네이버', status: '초안 완료' })
})

test('본문을 비우고 저장하면 그 슬롯만 미작성으로 돌아간다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')
  toCompanyView() // 토스
  fireEvent.click(item('문제를 해결한 경험'))
  fireEvent.change(screen.getByLabelText('자소서 본문'), { target: { value: '' } })
  fireEvent.click(screen.getByRole('button', { name: '저장' }))

  await waitFor(() => expect(preview('문제를 해결한 경험')).toBe('미작성'))
  expect(savedBodies()[0]).toMatchObject({ company: '토스', status: '미작성' })
})

test('글자 수는 작성한 리터럴 길이로 세고 초과를 경고한다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')

  fireEvent.click(screen.getByRole('button', { name: 'AI 초안 생성' }))
  await waitFor(() => expect(screen.getByLabelText('자소서 본문')).toHaveValue('AI가 쓴 초안'))
  expect(screen.getByText('8 / 700자')).toBeTruthy()

  // char_limit 10인 문항으로 옮기면 초과 경고
  fireEvent.click(item('문제를 해결한 경험'))
  fireEvent.change(screen.getByLabelText('자소서 본문'), {
    target: { value: '열두글자를넘기는본문입니다' },
  })
  expect(screen.getByText(/자 초과/)).toBeTruthy()
})

// {회사} 치환은 폐기됐다 — 화면 어디에도 토큰·삽입 버튼·미리보기가 남아 있으면 안 된다.
test('{회사} 토큰·삽입 버튼·미리보기가 남아 있지 않다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')

  expect(document.body.textContent).not.toContain('{회사}')
  expect(screen.queryByText(/삽입/)).toBeNull()
  expect(screen.queryByLabelText('답변 미리보기')).toBeNull()
})

test('검색이 문항 텍스트·유형·회사명으로 목록을 좁힌다', async () => {
  renderPage()
  await waitFor(() => expect(items()).toHaveLength(4))
  const box = screen.getByLabelText('문항 검색')

  fireEvent.change(box, { target: { value: '포부' } }) // 유형
  expect(items()).toHaveLength(1)
  expect(item('입사 후 포부')).toBeTruthy()

  fireEvent.change(box, { target: { value: '토스' } }) // 회사명(슬롯)
  expect(items()).toHaveLength(2)

  fireEvent.change(box, { target: { value: '한 문장으로' } }) // 문항 텍스트
  expect(items()).toHaveLength(1)

  fireEvent.change(box, { target: { value: '없는말' } })
  expect(screen.queryAllByRole('button', { name: /\?/ })).toHaveLength(0)
  expect(screen.getByText('해당하는 문항이 없어요.')).toBeTruthy()
})

// 재구조가 만든 데이터 소실 회귀(문항·기업 전환 = 본문 초기화)를 못박는다.
test('문항·기업을 옮겼다 돌아와도 저장 전 본문이 유지된다', async () => {
  renderPage()
  fireEvent.change(await screen.findByLabelText('자소서 본문'), {
    target: { value: '네이버에 쓰던 본문' },
  })

  await pick('작성할 기업', '토스') // 같은 문항, 다른 기업 슬롯
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('')
  fireEvent.change(screen.getByLabelText('자소서 본문'), { target: { value: '토스에 쓰던 본문' } })

  fireEvent.click(item('입사 후 포부'))
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('')

  fireEvent.click(item('지원한 이유'))
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('토스에 쓰던 본문')
  await pick('작성할 기업', '네이버')
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('네이버에 쓰던 본문')
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
  toCompanyView()
  await pick('기업 선택', '네이버')

  const badge = (label: string) => item(label).querySelector('.of-status')!
  expect(badge('입사 후 포부').textContent).toBe('작성 중')
  expect(badge('입사 후 포부').className).toContain('of-status--doing')
  expect(badge('지원한 이유').className).toContain('of-status--todo')

  await pick('기업 선택', '토스')
  expect(badge('문제를 해결한 경험').className).toContain('of-status--done')
})

// mutate 변수로 대상 슬롯을 넘기는 이유를 못박는다. 응답이 늦게 와도 "지금 보고 있는 슬롯"이
// 아니라 "요청한 슬롯"에 들어가야 하며, 어긋나면 남의 본문을 덮어쓰는 조용한 손실이 된다.
test('생성 중 다른 기업으로 옮겨도 초안은 요청한 슬롯에만 들어간다', async () => {
  let release!: () => void
  const pending = new Promise<void>((r) => (release = r))
  globalThis.fetch = vi.fn(async (url) => {
    if (!String(url).includes('/essays/draft')) return { ok: true, json: async () => store }
    await pending
    return { ok: true, json: async () => ({ question_id: 1, draft: 'AI가 쓴 초안' }) }
  }) as unknown as typeof fetch

  renderPage()
  await screen.findByLabelText('자소서 본문')

  fireEvent.click(screen.getByRole('button', { name: 'AI 초안 생성' })) // 네이버 슬롯에 요청
  await pick('작성할 기업', '토스') // 응답 전에 이동
  release()

  await waitFor(() => expect(screen.getByLabelText('자소서 본문')).toHaveValue(''))
  await pick('작성할 기업', '네이버')
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('AI가 쓴 초안')
})

async function pickTag(name: string) {
  await pick('유형 필터', name)
}

// 페이지네이션·필터를 태우려면 한 페이지(8개)를 넘는 풀이 필요하다.
function manyQuestions(n: number) {
  return Array.from({ length: n }, (_, i) => ({
    id: i + 1,
    tag: i % 2 ? '경험' : '역량',
    prompt: `${i + 1}번 문항은?`,
    char_limit: 500,
    slots: [{ company: '큰회사', deadline: '2026-08-01', content: '', status: '미작성' }],
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

test('유형·뷰·회사를 바꿔도 1페이지로 리셋된다', async () => {
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

// 슬롯 모델의 특수 케이스 두 개가 문항별 뷰에서 안 눌려 있었다: 어떤 기업도 안 쓰는 문항의
// '공통' 슬롯 저장, 그리고 고른 기업이 다음 문항에 없을 때의 폴백(잘못되면 slot이 undefined라
// 에디터가 통째로 사라진다).
test('문항별 뷰에서 공통 문항은 공통 슬롯으로 저장하고, 고른 기업은 문항을 옮겨도 남는다', async () => {
  renderPage()
  await screen.findByLabelText('자소서 본문')

  await pick('작성할 기업', '토스') // 문항 1을 토스로

  // 공통 문항(4번)엔 토스 슬롯이 없다 → 공통으로 폴백, 에디터는 살아 있어야 한다
  fireEvent.click(item('한 문장으로 소개'))
  expect(screen.getByRole('combobox', { name: '작성할 기업' }).textContent).toContain('공통')

  fireEvent.change(screen.getByLabelText('자소서 본문'), { target: { value: '저는 기록하는 개발자입니다' } })
  fireEvent.click(screen.getByRole('button', { name: '저장' }))

  await waitFor(() => expect(savedBodies()).toHaveLength(1))
  expect(savedBodies()[0]).toEqual({
    url: '/api/essays/questions/4/answer',
    company: '공통',
    content: '저는 기록하는 개발자입니다',
    status: '작성 중',
  })
  await waitFor(() => expect(preview('한 문장으로 소개')).toBe('저는 기록하는 개발자입니다'))

  // 문항 1로 돌아오면 아까 고른 토스가 그대로 — 공통으로 갈리지 않는다
  fireEvent.click(item('지원한 이유'))
  expect(screen.getByRole('combobox', { name: '작성할 기업' }).textContent).toContain('토스')
})

// 059220d가 고친 회귀에 못이 없었다: 목록을 클릭하지 않은 기본 선택 상태로 본문을 쓰다
// 페이지를 넘기면 에디터가 그 페이지 첫 문항으로 갈려 초안이 사라진 것처럼 보였다.
test('페이지를 넘겨도 기본 선택 문항과 쓰던 본문이 그대로다', async () => {
  store = manyQuestions(20) as unknown as typeof store
  renderPage()
  await waitFor(() => expect(items()).toHaveLength(8))

  const prompt = () => document.querySelector('.of-essay-panel__q')?.textContent
  expect(prompt()).toBe('1번 문항은?')
  fireEvent.change(screen.getByLabelText('자소서 본문'), { target: { value: '작성 중 본문' } })

  fireEvent.click(screen.getByRole('button', { name: '다음 페이지' }))
  expect(prompt()).toBe('1번 문항은?')
  expect(screen.getByLabelText('자소서 본문')).toHaveValue('작성 중 본문')
})
