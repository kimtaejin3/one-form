import { useMutation } from '@tanstack/react-query'
import { post } from '@/shared/api'

export type Draft = { essay_id: number; draft: string }

// 대상 문항을 mutate 변수로 넘긴다 — 생성 중에 다른 문항으로 옮겨도
// 초안은 요청한 문항(onSuccess의 두 번째 인자)에만 반영된다.
export function useGenerateDraft(onDone: (essayId: number, text: string) => void) {
  return useMutation({
    mutationFn: (essayId: number) => post<Draft>('/essays/draft', { essay_id: essayId }),
    onSuccess: (res, essayId) => onDone(essayId, res.draft),
  })
}
