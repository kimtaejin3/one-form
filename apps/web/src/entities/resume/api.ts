import { queryOptions } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { ResumeApplicationDocuments, ResumeEssayQuestion, ResumeTemplate } from './model'

export const resumeSeedQuery = queryOptions({
  queryKey: ['resume-seed'],
  queryFn: () => api<ResumeApplicationDocuments>('/resume/seed'),
})

export const resumeTemplatesQuery = queryOptions({
  queryKey: ['resume-templates'],
  queryFn: () => api<ResumeTemplate[]>('/resume/templates'),
})

export const resumeEssayQuestionsQuery = queryOptions({
  queryKey: ['resume-essay-questions'],
  queryFn: () => api<ResumeEssayQuestion[]>('/resume/essay-questions'),
})
