import { useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { EssayListItem, essaysQuery } from '@/entities/essay'
import { EssayEditor } from '@/features/generate-draft'
import CompanyTabs from './CompanyTabs'

// 회사 → 문항 → 작성의 2단 선택. 선택값은 렌더 중 목록과 맞춰 해석하므로
// 회사를 바꾸면 문항 선택도 자연히 그 회사의 첫 문항으로 돌아간다(useEffect 불필요).
export default function EssaysPage() {
  const { data: essays } = useSuspenseQuery(essaysQuery)
  const [pickedCompany, setPickedCompany] = useState<string | null>(null)
  const [pickedId, setPickedId] = useState<number | null>(null)
  // 작성 본문은 문항 id별로 페이지가 들고 있는다 — 문항을 옮겼다 돌아와도 남아 있어야 한다.
  const [texts, setTexts] = useState<Record<number, string>>({})

  const companies = [...new Set(essays.map((e) => e.company))]
  const company = pickedCompany && companies.includes(pickedCompany) ? pickedCompany : companies[0]
  const questions = essays
    .filter((e) => e.company === company)
    .sort((a, b) => a.deadline.localeCompare(b.deadline)) // 마감 임박순
  const selected = questions.find((e) => e.id === pickedId) ?? questions[0]

  if (!selected) return <p className="of-mono">작성할 자소서 문항이 없어요.</p>

  return (
    <div className="stack">
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
          text={texts[selected.id] ?? ''}
          onChangeText={(id, text) => setTexts((prev) => ({ ...prev, [id]: text }))}
        />
      </div>
    </div>
  )
}
