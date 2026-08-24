import { queryOptions } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { ResumeEssaySet, ResumeState, ResumeTemplate } from './model'

export const resumeSeedQuery = queryOptions({
  queryKey: ['resume-seed'],
  queryFn: () => api<ResumeState>('/resume/seed'),
})

export const resumeTemplatesQuery = queryOptions({
  queryKey: ['resume-templates'],
  queryFn: () => api<ResumeTemplate[]>('/resume/templates'),
})

// 기업별 자소서 세트(질문뱅크) — 세트를 고르면 그 기업 자소서 문항이 구성된다.
export const resumeEssaySetsQuery = queryOptions({
  queryKey: ['resume-essay-sets'],
  queryFn: () => api<ResumeEssaySet[]>('/resume/essay-sets'),
})
