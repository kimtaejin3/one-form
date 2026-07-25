import { useMutation, useQueryClient } from '@tanstack/react-query'
import { questionsQuery, type Question } from '@/entities/essay'
import { put, type components } from '@/shared/api'

type AnswerUpdate = components['schemas']['AnswerUpdate']

/**
 * 답변 저장. 저장 단위는 (기업 × 문항) 슬롯이라 바디에 company가 들어가고, 같은 문항이라도
 * 다른 기업 답변은 건드리지 않는다. 저장 후 문항 풀을 invalidate해 목록·진행 요약이 다시 그려진다.
 */
export function useSaveAnswer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ questionId, ...body }: AnswerUpdate & { questionId: number }) =>
      put<Question>(`/essays/questions/${questionId}/answer`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: questionsQuery.queryKey }),
  })
}
