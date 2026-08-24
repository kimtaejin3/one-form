import { useMutation } from '@tanstack/react-query'
import { post } from '@/shared/api'
import type { ResumeEssayDraftResponse, ResumeState } from '@/entities/resume'

// AI 초안 — 선택 문항과 프로필을 백엔드에 넘겨 초안을 받는다.
export function useEssayDraft(onDraft: (index: number, draft: string, note: string) => void) {
  return useMutation({
    mutationFn: (v: {
      index: number
      question: string
      char_limit: number | null
      state: ResumeState
    }) =>
      post<ResumeEssayDraftResponse>('/resume/essay-draft', {
        question: v.question,
        char_limit: v.char_limit,
        state: v.state,
      }),
    onSuccess: (res, vars) => onDraft(vars.index, res.draft, res.note),
  })
}
