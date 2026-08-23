import { useMutation } from '@tanstack/react-query'
import { post } from '@/shared/api'
import type { ResumeState, ResumeMaterial, ResumeChatResponse } from '@/entities/resume'

export function useResumeChat(onState: (s: ResumeState, reply: string) => void) {
  return useMutation({
    mutationFn: (v: { state: ResumeState; materials: ResumeMaterial[]; message: string }) =>
      post<ResumeChatResponse>('/resume/chat', v),
    onSuccess: (res) => onState(res.state, res.reply),
  })
}
