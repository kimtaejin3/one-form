import { useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { Dropdown, Input, Pagination } from '@one-form/design-system'
import { COMMON, QuestionListItem, questionsQuery, slotKey, type Question } from '@/entities/essay'
import EssayEditor from './EssayEditor'

const VIEWS = [
  { key: 'question', label: '문항별' },
  { key: 'company', label: '기업별' },
] as const
type View = (typeof VIEWS)[number]['key']

type CompanySummary = {
  name: string
  deadline: string
  questionCount: number
  doneCount: number
  writtenCount: number
}

const ALL_TAGS = '전체 유형'
const PAGE_SIZE = 8

function matches(q: Question, needle: string) {
  return q.prompt.toLowerCase().includes(needle.trim().toLowerCase())
}

/** 남은 날짜는 시각이 아니라 달력 일수로 센다 — 'sv-SE'는 로컬 날짜를 YYYY-MM-DD로 준다. */
function dday(deadline: string) {
  if (!deadline) return '상시'
  const days = Math.round(
    (Date.parse(deadline) - Date.parse(new Date().toLocaleDateString('sv-SE'))) / 86_400_000,
  )
  return days > 0 ? `D-${days}` : days === 0 ? 'D-DAY' : `D+${-days}`
}

/**
 * 자소서 허브 — 문항은 유니크하지만 답변은 (문항 × 기업) 슬롯마다 별개다. 문항별 뷰는 문항을 고른 뒤
 * 에디터에서 기업을 고르고, 기업별 뷰는 회사를 고정한 채 그 회사 슬롯을 편집한다. 서버 상태는
 * 문항 풀 쿼리 하나뿐이고 검색·유형·뷰·회사·페이지·선택은 useState, 목록·슬롯은 렌더 중 파생한다.
 */
export default function EssaysPage() {
  const { data: questions } = useSuspenseQuery(questionsQuery)
  const [search, setSearch] = useState('')
  const [view, setView] = useState<View>('question')
  const [pickedTag, setPickedTag] = useState(ALL_TAGS)
  const [pickedCompany, setPickedCompany] = useState('')
  const [pickedSlot, setPickedSlot] = useState('') // 문항별 뷰 에디터의 기업
  const [pickedPage, setPickedPage] = useState(1)
  const [pickedId, setPickedId] = useState<number | null>(null)
  // 편집 중 본문은 슬롯 키((문항, 기업))별로 페이지가 들고 있는다 — 옮겼다 돌아와도 남아 있어야 한다.
  // 손대지 않은 슬롯은 서버에 저장된 답변을 그대로 보여준다.
  const [edits, setEdits] = useState<Record<string, string>>({})

  // 슬롯이 곧 기업 목록이다(마감 임박순). 공통 슬롯은 회사가 아니므로 뺀다.
  const slots = questions.flatMap((q) => q.slots)
  const byName = new Map(slots.filter((s) => s.company !== COMMON).map((s) => [s.company, s]))
  const companies = [...byName.values()].sort((a, b) =>
    (a.deadline || '9999-12-31').localeCompare(b.deadline || '9999-12-31'),
  )
  const shownCompanies = companies.filter((item) =>
    item.company.toLowerCase().includes(search.trim().toLowerCase()),
  )
  const company =
    view === 'company'
      ? (shownCompanies.find((item) => item.company === pickedCompany) ?? shownCompanies[0])
      : undefined
  const companySummaries: CompanySummary[] = shownCompanies.map((item) => {
    const companySlots = slots.filter((slot) => slot.company === item.company)
    return {
      name: item.company,
      deadline: item.deadline,
      questionCount: companySlots.length,
      doneCount: companySlots.filter((slot) => slot.status === '초안 완료').length,
      writtenCount: companySlots.filter((slot) => slot.status !== '미작성').length,
    }
  })

  // 유형 필터는 문항별 뷰 전용 — 기업별에선 회사 선택이 주 필터라 유형까지 겹치지 않는다.
  const tags = [ALL_TAGS, ...new Set(questions.map((q) => q.tag))]
  const tag = tags.includes(pickedTag) ? pickedTag : ALL_TAGS

  const pool =
    view === 'company'
      ? company
        ? questions.filter((q) => q.slots.some((s) => s.company === company.company))
        : []
      : questions
  const list = pool
    .filter((q) => company || tag === ALL_TAGS || q.tag === tag)
    .filter((q) => view === 'company' || matches(q, search))
  const done = slots.filter((s) => s.status === '초안 완료').length

  // 필터가 바뀌어 목록이 짧아지면 페이지도 따라 접힌다(렌더 중 보정 — useEffect 불필요).
  const totalPages = Math.max(1, Math.ceil(list.length / PAGE_SIZE))
  const page = Math.min(pickedPage, totalPages)
  const shown = list.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  // 고른 문항이 다른 페이지에 있어도 에디터는 그대로 둔다(작성 중 본문 보호).
  // 안 고른 기본 선택은 페이지 무관하게 목록 첫 문항으로 고정 — 페이지 넘겨도 에디터가 안 갈린다.
  const selected = list.find((q) => q.id === (pickedId ?? list[0]?.id)) ?? shown[0]
  // 기업별은 그 회사 슬롯으로 고정, 문항별은 고른 기업(없으면 첫 슬롯).
  const slot = company
    ? selected?.slots.find((s) => s.company === company.company)
    : (selected?.slots.find((s) => s.company === pickedSlot) ?? selected?.slots[0])

  return (
    <div className="stack">
      <div className="of-essay-view-switch" role="group" aria-label="작성 기준">
        {VIEWS.map((v) => (
          <button
            key={v.key}
            type="button"
            aria-label={v.label}
            aria-pressed={v.key === view}
            className={`of-essay-view-option${v.key === view ? ' of-essay-view-option--on' : ''}`}
            onClick={() => {
              setView(v.key)
              setSearch('')
              setPickedPage(1)
            }}
          >
            <strong>{v.label} 작성</strong>
            <span>
              {v.key === 'question'
                ? `${questions.length}개 문항을 유형별로 작성`
                : `${companies.length}개 기업의 문항을 모아 작성`}
            </span>
          </button>
        ))}
      </div>

      <div className="of-essay-toolbar">
        <Input
          type="search"
          aria-label={view === 'question' ? '문항 내용 검색' : '기업명 검색'}
          placeholder={view === 'question' ? '문항 내용으로 검색' : '기업명으로 검색'}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPickedPage(1)
          }}
        />
        {view === 'question' && (
          <Dropdown
            label="유형 필터"
            options={tags.map((t) => ({ value: t, label: t }))}
            value={tag}
            onChange={(v) => {
              setPickedTag(v)
              setPickedPage(1)
            }}
          />
        )}
        <p className="of-essay-progress">
          진행: 기업별 문항 {slots.length}개 중 {done} 완료
        </p>
      </div>

      {view === 'company' && (
        <section className="of-essay-company-board" aria-label="지원 기업 현황">
          <div className="of-essay-company-board__heading">
            <div>
              <h2>지원 기업</h2>
              <p>기업을 고르면 해당 회사의 문항만 모아 볼 수 있어요.</p>
            </div>
            <span className="of-mono">{companySummaries.length}개 기업</span>
          </div>
          <div className="of-essay-company-board__grid">
            {companySummaries.map((summary) => {
              const selectedCompany = summary.name === company?.company
              const missingCount = summary.questionCount - summary.writtenCount
              return (
                <button
                  key={summary.name}
                  type="button"
                  className={`of-essay-company-card${selectedCompany ? ' of-essay-company-card--on' : ''}`}
                  aria-pressed={selectedCompany}
                  onClick={() => {
                    setPickedCompany(summary.name)
                    setPickedPage(1)
                  }}
                >
                  <span className="of-essay-company-card__top">
                    <strong>{summary.name}</strong>
                    <span className="of-mono">{dday(summary.deadline)}</span>
                  </span>
                  <span className="of-essay-company-card__progress">
                    {summary.doneCount}/{summary.questionCount} 완료
                  </span>
                  <span className="of-essay-company-card__meta">
                    {missingCount > 0 ? `미작성 ${missingCount}개` : '모든 문항 작성'} ·{' '}
                    {summary.deadline ? `마감 ${summary.deadline}` : '상시 채용'}
                  </span>
                </button>
              )
            })}
            {companySummaries.length === 0 && (
              <p className="of-essay-empty of-mono">일치하는 기업이 없어요.</p>
            )}
          </div>
          {company && (
            <div className="row of-essay-company-filter">
              <Dropdown
                label="기업 선택"
                options={shownCompanies.map((c) => ({ value: c.company, label: c.company }))}
                value={company.company}
                onChange={(v) => {
                  setPickedCompany(v)
                  setPickedPage(1)
                }}
              />
              <span className="of-mono">
                {company.deadline
                  ? `마감 ${company.deadline} · ${dday(company.deadline)}`
                  : '상시 채용'}
              </span>
            </div>
          )}
        </section>
      )}

      <div className="of-essay-split">
        <div className="stack">
          <div className="of-essay-list">
            {list.length === 0 && <p className="of-essay-empty of-mono">해당하는 문항이 없어요.</p>}
            {shown.map((question) => (
              <QuestionListItem
                key={question.id}
                question={question}
                slot={company && question.slots.find((s) => s.company === company.company)}
                selected={question.id === selected?.id}
                onSelect={() => setPickedId(question.id)}
              />
            ))}
          </div>
          <Pagination
            label="문항 목록 페이지"
            page={page}
            totalPages={totalPages}
            onChange={setPickedPage}
          />
        </div>

        {selected && slot && (
          <EssayEditor
            question={selected}
            slot={slot}
            companies={company ? undefined : selected.slots.map((s) => s.company)}
            onPickCompany={company ? undefined : setPickedSlot}
            text={edits[slotKey(selected.id, slot.company)] ?? slot.content}
            onChangeText={(key, text) => setEdits((prev) => ({ ...prev, [key]: text }))}
          />
        )}
      </div>
    </div>
  )
}
