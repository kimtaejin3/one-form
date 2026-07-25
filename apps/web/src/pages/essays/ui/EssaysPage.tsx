import { useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { EssayListItem, essaysQuery } from '@/entities/essay'
import CompanyTabs, { ALL_COMPANIES } from './CompanyTabs'
import EssayEditor from './EssayEditor'

// 전체 문항이 기본이고, 회사 필터는 좁혀 보는 수단이다. 선택값은 렌더 중 목록과 맞춰
// 해석하므로 필터를 바꾸면 문항 선택도 자연히 그 목록의 첫 문항으로 돌아간다(useEffect 불필요).
export default function EssaysPage() {
  const { data: essays } = useSuspenseQuery(essaysQuery)
  const [pickedCompany, setPickedCompany] = useState(ALL_COMPANIES)
  const [pickedId, setPickedId] = useState<number | null>(null)
  // 편집 중 본문은 문항 id별로 페이지가 들고 있는다 — 문항을 옮겼다 돌아와도 남아 있어야 한다.
  // 손대지 않은 문항은 서버에 저장된 답변을 그대로 보여준다.
  const [edits, setEdits] = useState<Record<number, string>>({})

  const companies = [ALL_COMPANIES, ...new Set(essays.map((e) => e.company))]
  const company = companies.includes(pickedCompany) ? pickedCompany : ALL_COMPANIES
  const questions = essays
    .filter((e) => company === ALL_COMPANIES || e.company === company)
    .sort((a, b) => a.deadline.localeCompare(b.deadline)) // 마감 임박순
  const selected = questions.find((e) => e.id === pickedId) ?? questions[0]
  const done = essays.filter((e) => e.status === '초안 완료').length

  if (!selected) return <p className="of-mono">작성할 자소서 문항이 없어요.</p>

  return (
    <div className="stack">
      <p className="of-essay-progress">
        진행: {essays.length}개 중 {done} 완료
      </p>

      <CompanyTabs companies={companies} selected={company} onSelect={setPickedCompany} />

      <div
        className="of-essay-split"
        role="tabpanel"
        id="essay-company-panel"
        aria-labelledby="essay-company-tab"
      >
        <div className="of-essay-list">
          {questions.map((essay) => (
            <EssayListItem
              key={essay.id}
              essay={essay}
              selected={essay.id === selected.id}
              onSelect={() => setPickedId(essay.id)}
            />
          ))}
        </div>

        <EssayEditor
          essay={selected}
          text={edits[selected.id] ?? selected.answer}
          onChangeText={(id, text) => setEdits((prev) => ({ ...prev, [id]: text }))}
        />
      </div>
    </div>
  )
}
