import { useMutation } from '@tanstack/react-query'
import { post, type components } from '@/shared/api'

type DraftResponse = components['schemas']['DraftResponse']

// 대상 문항을 mutate 변수로 넘긴다 — 생성 중에 다른 문항으로 옮겨도
// 초안은 요청한 문항(onSuccess의 두 번째 인자)에만 반영된다.
export function useGenerateDraft(onDone: (questionId: number, text: string) => void) {
  return useMutation({
    mutationFn: (questionId: number) =>
      post<DraftResponse>('/essays/draft', { question_id: questionId }),
    onSuccess: (res, questionId) => onDone(questionId, res.draft),
  })
}
