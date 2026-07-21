import { useMutation } from '@tanstack/react-query'
import { post } from '@/shared/api'

export type Draft = { essay_id: number; draft: string }

export function useGenerateDraft(essayId: number, onDone: (text: string) => void) {
  return useMutation({
    mutationFn: () => post<Draft>('/essays/draft', { essay_id: essayId }),
    onSuccess: (res) => onDone(res.draft),
  })
}
