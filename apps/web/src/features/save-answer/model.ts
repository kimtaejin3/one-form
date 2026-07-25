import { useMutation, useQueryClient } from '@tanstack/react-query'
import { essaysQuery, type Essay } from '@/entities/essay'
import { put, type components } from '@/shared/api'

type AnswerUpdate = components['schemas']['AnswerUpdate']

/**
 * 문항 답변 저장. 저장이 끝나면 목록을 invalidate해 리스트 미리보기와
 * 진행 요약(완료 수)이 서버 값으로 다시 그려진다.
 */
export function useSaveAnswer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ essayId, ...body }: AnswerUpdate & { essayId: number }) =>
      put<Essay>(`/essays/${essayId}/answer`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: essaysQuery.queryKey }),
  })
}
