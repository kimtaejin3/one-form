import { useSuspenseQuery } from '@tanstack/react-query'
import { essaysQuery } from '@/entities/essay'
import { EssayCard } from '@/features/generate-draft'

export default function EssaysPage() {
  const { data: essays } = useSuspenseQuery(essaysQuery)

  return (
    <div className="stack">
      {essays.map((essay) => (
        <EssayCard key={essay.id} essay={essay} />
      ))}
    </div>
  )
}
