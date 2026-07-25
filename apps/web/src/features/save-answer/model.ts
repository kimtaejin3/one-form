import { useMutation, useQueryClient } from '@tanstack/react-query'
import { questionsQuery, type Question } from '@/entities/essay'
import { put, type components } from '@/shared/api'

type AnswerUpdate = components['schemas']['AnswerUpdate']

/**
 * 답변 저장. 저장은 기업이 아니라 **문항 id** 기준이라 그 문항을 묻는 모든 기업에 함께 반영된다.
 * 저장 후 문항 풀을 invalidate해 미리보기와 진행 요약이 서버 값으로 다시 그려진다.
 */
export function useSaveAnswer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ questionId, ...body }: AnswerUpdate & { questionId: number }) =>
      put<Question>(`/essays/questions/${questionId}/answer`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: questionsQuery.queryKey }),
  })
}
