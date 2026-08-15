import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, expect, test, vi } from 'vitest'
import CompanyIntelligence from './CompanyIntelligence'
import type { CompanyMatch, Intelligence } from '@/features/analyze-company'

const SITE_SOURCE = {
  id: 1,
  kind: 'official_site' as const,
  url: 'https://example.com',
  title: '예시 공식 홈페이지',
  publisher: 'example.com',
  published_at: null,
  fetched_at: '2026-08-01T00:00:00Z',
  trust_level: 'primary' as const,
  changed: false,
}

const JOB_SOURCE = {
  ...SITE_SOURCE,
  id: 2,
  kind: 'job_posting' as const,
  url: 'https://jobs.example.com/1',
  title: '백엔드 채용 공고',
  publisher: 'jobs.example.com',
  trust_level: 'user_provided' as const,
}

const JOB = {
  id: 7,
  source_id: 2,
  title: '백엔드 엔지니어',
  role_category: '백엔드 개발',
  location: '서울',
  employment: '정규직',
  deadline: '상시채용',
  description: '결제 시스템을 만듭니다.',
  requirements: ['Python'],
  preferred: ['Kubernetes'],
  core_skills: ['Python', 'Kubernetes'],
  problem_types: ['대용량 트래픽 처리'],
}

const MATCHES: CompanyMatch[] = [
  {
    job_id: 7,
    company_need: 'Python',
    profile_evidence: 'OO페이 · 백엔드 엔지니어 인턴',
    match_type: 'strength',
    score: 90,
    reason: "OO페이 · 백엔드 엔지니어 인턴에서 'Python' 사용 — 결제 실패율 개선",
    source_ids: [2],
  },
  {
    job_id: 7,
    company_need: 'Kubernetes',
    profile_evidence: '',
    match_type: 'gap',
    score: 0,
    reason: "'Kubernetes'을(를) 쓴 경력·프로젝트가 프로필에 없습니다.",
    source_ids: [2],
  },
]

function intelligence(overrides: Partial<Intelligence> = {}): Intelligence {
  return {
    name: '예시',
    normalized_name: '예시',
    domain: '',
    summary: { text: '물류 자동화 소프트웨어 기업.', source_ids: [1] },
    stage: { text: '비상장', source_ids: [1] },
    business_areas: [{ text: '물류 자동화', source_ids: [1] }],
    products: [{ text: '로봇 WMS', source_ids: [1] }],
    signals: [
      {
        label: '로봇 사업 진출',
        detail: '2026년 로봇 사업을 시작했다.',
        signal_type: 'business',
        confidence: 0.8,
        evidence_quote: '2026년 로봇 사업을 시작했습니다.',
        source_ids: [1],
      },
    ],
    jobs: [],
    sources: [SITE_SOURCE],
    source_count: 1,
    manual_urls: [],
    status: 'ready',
    warnings: [],
    needs_review: [],
    last_analyzed_at: '2026-08-01T00:00:00Z',
    fresh_until: '2026-08-02T00:00:00Z',
    is_stale: false,
    ...overrides,
  }
}

function mockApi(body: Intelligence, matches: CompanyMatch[] = MATCHES) {
  globalThis.fetch = vi.fn((url) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(String(url).includes('/matches') ? matches : body),
    }),
  ) as unknown as typeof fetch
}

function calls() {
  return (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls
}

function requestBodies() {
  return calls()
    .filter((c) => c[1] && (c[1] as RequestInit).body)
    .map((c) => JSON.parse(String((c[1] as RequestInit).body)))
}

function renderWidget() {
  const qc = new QueryClient({
    defaultOptions: { mutations: { retry: false }, queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <CompanyIntelligence />
    </QueryClientProvider>,
  )
}

function submit(name: string, jobUrl?: string) {
  fireEvent.change(screen.getByLabelText('기업명'), { target: { value: name } })
  if (jobUrl) {
    fireEvent.change(screen.getByLabelText('채용공고 URL'), { target: { value: jobUrl } })
  }
  fireEvent.click(screen.getByRole('button', { name: '분석' }))
}

const tab = (name: string) => screen.getByRole('tab', { name })

beforeEach(() => {
  vi.restoreAllMocks()
})

test('개요와 사업/제품 탭을 근거 칩과 함께 보여준다', async () => {
  mockApi(intelligence())
  renderWidget()
  submit('예시')

  await waitFor(() => expect(screen.getByText('물류 자동화 소프트웨어 기업.')).toBeTruthy())
  expect(screen.getByText('물류 자동화')).toBeTruthy()
  expect(screen.getByText('로봇 WMS')).toBeTruthy()
  expect(screen.getByText('비상장')).toBeTruthy()

  const chip = screen.getAllByTitle('예시 공식 홈페이지')[0] as HTMLAnchorElement
  expect(chip.href).toBe('https://example.com/')
  expect(chip.target).toBe('_blank')
  expect(chip.rel).toContain('noopener')
})

test('탭을 바꾸면 해당 내용만 보인다', async () => {
  mockApi(intelligence())
  renderWidget()
  submit('예시')

  await waitFor(() => expect(screen.getByText('물류 자동화')).toBeTruthy())

  fireEvent.click(tab('최근 신호'))
  expect(screen.getByText(/2026년 로봇 사업을 시작했다/)).toBeTruthy()
  expect(screen.queryByText('로봇 WMS')).toBeNull()

  fireEvent.click(tab('사업/제품'))
  expect(screen.getByText('로봇 WMS')).toBeTruthy()
})

test('빈 기업명은 요청하지 않는다', () => {
  mockApi(intelligence())
  renderWidget()
  submit('   ')

  expect(globalThis.fetch).not.toHaveBeenCalled()
})

test('공고 URL을 함께 보내고, 다시 분석은 force_refresh로 요청한다', async () => {
  mockApi(intelligence())
  renderWidget()
  submit('예시', 'https://jobs.example.com/1')

  await waitFor(() => expect(screen.getByText('다시 분석')).toBeTruthy())
  fireEvent.click(screen.getByText('다시 분석'))

  await waitFor(() => expect(requestBodies()).toHaveLength(2))
  expect(requestBodies()[0].job_url).toBe('https://jobs.example.com/1')
  expect(requestBodies()[1].force_refresh).toBe(true)
})

test('직무 분석과 내 경험 매칭 탭이 선택한 공고를 따라간다', async () => {
  const second = { ...JOB, id: 8, title: '프론트엔드 엔지니어', core_skills: ['React'] }
  mockApi(
    intelligence({ jobs: [JOB, second], sources: [SITE_SOURCE, JOB_SOURCE], source_count: 2 }),
  )
  renderWidget()
  submit('예시', 'https://jobs.example.com/1')

  await waitFor(() => expect(screen.getByText('물류 자동화')).toBeTruthy())

  fireEvent.click(tab('직무 분석'))
  expect(screen.getByText('백엔드 개발 · 서울 · 정규직 · 상시채용')).toBeTruthy()
  expect(screen.getByText('대용량 트래픽 처리')).toBeTruthy()

  fireEvent.click(tab('내 경험 매칭'))
  await waitFor(() => expect(screen.getByText('강점 1 · 갭 1')).toBeTruthy())
  expect(screen.getByText(/OO페이 · 백엔드 엔지니어 인턴에서 'Python' 사용/)).toBeTruthy()
  expect(screen.getByText(/'Kubernetes'을\(를\) 쓴 경력·프로젝트가 프로필에 없습니다/)).toBeTruthy()
  expect(calls().some((c) => String(c[0]).includes('job_id=7'))).toBe(true)

  // 다른 공고를 고르면 그 공고 기준으로 다시 조회한다
  fireEvent.click(tab('직무 분석'))
  fireEvent.click(screen.getByRole('tab', { name: '프론트엔드 엔지니어' }))
  fireEvent.click(tab('내 경험 매칭'))
  await waitFor(() => expect(calls().some((c) => String(c[0]).includes('job_id=8'))).toBe(true))
})

test('공고가 없으면 직무·매칭 탭이 안내를 보여준다', async () => {
  mockApi(intelligence())
  renderWidget()
  submit('예시')

  await waitFor(() => expect(screen.getByText('물류 자동화')).toBeTruthy())

  fireEvent.click(tab('직무 분석'))
  expect(screen.getByText(/채용공고 URL을 입력하면 직무별 핵심 역량/)).toBeTruthy()

  fireEvent.click(tab('내 경험 매칭'))
  expect(screen.getByText(/채용공고 URL을 입력하면 그 직무의 요구 역량/)).toBeTruthy()
  expect(calls().some((c) => String(c[0]).includes('/matches'))).toBe(false)
})

test('partial이면 경고와 확인 필요 항목을 노출한다', async () => {
  mockApi(
    intelligence({
      status: 'partial',
      warnings: ['manual 출처 수집 실패: 연결 시간 초과'],
      needs_review: ['근거 출처가 없어 제외한 신호: 채용 확대'],
    }),
  )
  renderWidget()
  submit('예시')

  await waitFor(() => expect(screen.getByRole('status')).toBeTruthy())
  expect(screen.getByText(/연결 시간 초과/)).toBeTruthy()
  expect(screen.getByText(/확인 필요 · 근거 출처가 없어/)).toBeTruthy()
})

test('오래된 결과는 다시 분석하라고 알린다', async () => {
  mockApi(intelligence({ is_stale: true }))
  renderWidget()
  submit('예시')

  await waitFor(() => expect(screen.getByText('오래된 분석 결과')).toBeTruthy())
  expect(screen.getByText(/최신성 기준을 지났습니다/)).toBeTruthy()
})

test('원문이 바뀐 출처를 표시한다', async () => {
  mockApi(intelligence({ sources: [{ ...SITE_SOURCE, changed: true }] }))
  renderWidget()
  submit('예시')

  await waitFor(() => expect(screen.getAllByText('변경됨').length).toBeGreaterThan(0))
  expect(screen.getByText(/직전 분석 이후 원문이 바뀐 출처 1건/)).toBeTruthy()
})

test('출처를 못 찾으면 사실을 지어내지 않고 안내만 보여준다', async () => {
  mockApi(
    intelligence({
      status: 'failed',
      summary: null,
      stage: null,
      business_areas: [],
      products: [],
      signals: [],
      sources: [],
      source_count: 0,
      warnings: ['공식 출처를 찾지 못했습니다. 기업 공식 홈페이지나 채용공고 URL을 입력해 주세요.'],
    }),
  )
  renderWidget()
  submit('듣도보도못한기업')

  await waitFor(() => expect(screen.getByText('확인된 출처 없음')).toBeTruthy())
  expect(screen.getByText('수집된 출처가 없습니다.')).toBeTruthy()
  expect(screen.getByText('확인된 사업·제품 정보가 없습니다.')).toBeTruthy()
})
