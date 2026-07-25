import { useMutation } from '@tanstack/react-query'
import { post, type components } from '@/shared/api'

type DraftResponse = components['schemas']['DraftResponse']

// 대상 슬롯(문항 × 기업)을 mutate 변수로 넘긴다 — 생성 중에 다른 문항·기업으로 옮겨도
// 초안은 요청한 슬롯(onSuccess의 두 번째 인자)에만 반영된다.
export function useGenerateDraft(onDone: (key: string, text: string) => void) {
  return useMutation({
    mutationFn: ({ questionId }: { questionId: number; key: string }) =>
      post<DraftResponse>('/essays/draft', { question_id: questionId }),
    onSuccess: (res, vars) => onDone(vars.key, res.draft),
  })
}
