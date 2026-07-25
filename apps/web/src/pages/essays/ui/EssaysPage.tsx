import { useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { Dropdown, Input, Pagination } from '@one-form/design-system'
import { QuestionListItem, questionsQuery, type Question } from '@/entities/essay'
import EssayEditor from './EssayEditor'

const VIEWS = [
  { key: 'question', label: '문항별' },
  { key: 'company', label: '기업별' },
] as const
type View = (typeof VIEWS)[number]['key']

const ALL_TAGS = '전체 유형'
const PAGE_SIZE = 8

/** 검색은 문항 텍스트·유형·이 문항을 쓰는 회사명까지 훑는다. */
function matches(q: Question, needle: string) {
  const hay = [q.prompt, q.tag, ...q.companies.map((c) => c.name)].join(' ').toLowerCase()
  return hay.includes(needle.trim().toLowerCase())
}

/** 남은 날짜는 시각이 아니라 달력 일수로 센다 — 'sv-SE'는 로컬 날짜를 YYYY-MM-DD로 준다. */
function dday(deadline: string) {
  const days = Math.round(
    (Date.parse(deadline) - Date.parse(new Date().toLocaleDateString('sv-SE'))) / 86_400_000,
  )
  return days > 0 ? `D-${days}` : days === 0 ? 'D-DAY' : `D+${-days}`
}

/**
 * 자소서 허브 — 답변은 문항에 붙어 재사용되므로 문항 풀이 기본이고, 기업은 그 풀을 보는
 * 또 하나의 렌즈(그 회사가 묻는 문항 + 마감)일 뿐이다. 서버 상태는 문항 풀 쿼리 하나뿐이고
 * 검색·유형·뷰·회사·페이지·선택은 useState, 목록·페이지 슬라이스·선택·치환은 렌더 중 파생한다.
 */
export default function EssaysPage() {
  const { data: questions } = useSuspenseQuery(questionsQuery)
  const [search, setSearch] = useState('')
  const [view, setView] = useState<View>('question')
  const [pickedTag, setPickedTag] = useState(ALL_TAGS)
  const [pickedCompany, setPickedCompany] = useState('')
  const [pickedPage, setPickedPage] = useState(1)
  const [pickedId, setPickedId] = useState<number | null>(null)
  // 편집 중 본문은 문항 id별로 페이지가 들고 있는다 — 문항을 옮겼다 돌아와도 남아 있어야 한다.
  // 손대지 않은 문항은 서버에 저장된 답변을 그대로 보여준다.
  const [edits, setEdits] = useState<Record<number, string>>({})

  // 문항이 들고 있는 기업 목록을 그대로 뒤집어 회사 목록을 만든다(마감 임박순).
  const byName = new Map(questions.flatMap((q) => q.companies).map((c) => [c.name, c]))
  const companies = [...byName.values()].sort((a, b) => a.deadline.localeCompare(b.deadline))
  const company = view === 'company' ? (byName.get(pickedCompany) ?? companies[0]) : undefined

  // 유형 필터는 문항별 뷰 전용 — 기업별에선 회사 선택이 주 필터라 유형까지 겹치지 않는다.
  const tags = [ALL_TAGS, ...new Set(questions.map((q) => q.tag))]
  const tag = tags.includes(pickedTag) ? pickedTag : ALL_TAGS

  const pool = company
    ? questions.filter((q) => q.companies.some((c) => c.name === company.name))
    : questions
  const list = pool
    .filter((q) => company || tag === ALL_TAGS || q.tag === tag)
    .filter((q) => matches(q, search))
  const done = questions.filter((q) => q.status === '초안 완료').length

  // 필터가 바뀌어 목록이 짧아지면 페이지도 따라 접힌다(렌더 중 보정 — useEffect 불필요).
  const totalPages = Math.max(1, Math.ceil(list.length / PAGE_SIZE))
  const page = Math.min(pickedPage, totalPages)
  const shown = list.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  // 고른 문항이 다른 페이지에 있어도 에디터는 그대로 둔다(작성 중 본문 보호).
  const selected = list.find((q) => q.id === pickedId) ?? shown[0]

  return (
    <div className="stack">
      <div className="of-essay-toolbar">
        <Input
          type="search"
          aria-label="문항 검색"
          placeholder="문항·유형·회사명으로 검색"
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
        <div className="job-filters" role="tablist" aria-label="보기 방식">
          {VIEWS.map((v) => (
            <button
              key={v.key}
              type="button"
              role="tab"
              aria-selected={v.key === view}
              aria-controls="essay-view-panel"
              className={`filter-chip${v.key === view ? ' filter-chip--on' : ''}`}
              onClick={() => {
                setView(v.key)
                setPickedPage(1)
              }}
            >
              {v.label}
            </button>
          ))}
        </div>
        <p className="of-essay-progress">
          진행: 전체 {questions.length}문항 중 {done} 완료
        </p>
      </div>

      {view === 'company' && company && (
        <div className="row">
          <Dropdown
            label="기업 선택"
            options={companies.map((c) => ({ value: c.name, label: c.name }))}
            value={company.name}
            onChange={(v) => {
              setPickedCompany(v)
              setPickedPage(1)
            }}
          />
          <span className="of-mono">
            마감 {company.deadline} · {dday(company.deadline)}
          </span>
        </div>
      )}

      <div className="of-essay-split" role="tabpanel" id="essay-view-panel">
        <div className="stack">
          <div className="of-essay-list">
            {list.length === 0 && <p className="of-essay-empty of-mono">해당하는 문항이 없어요.</p>}
            {shown.map((question) => (
              <QuestionListItem
                key={question.id}
                question={question}
                company={company?.name}
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

        {selected && (
          <EssayEditor
            question={selected}
            company={company?.name}
            text={edits[selected.id] ?? selected.answer}
            onChangeText={(id, text) => setEdits((prev) => ({ ...prev, [id]: text }))}
          />
        )}
      </div>
    </div>
  )
}
