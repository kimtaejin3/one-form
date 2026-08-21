import { queryOptions } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { ResumeState, ResumeTemplate } from './model'

export const resumeSeedQuery = queryOptions({
  queryKey: ['resume-seed'],
  queryFn: () => api<ResumeState>('/resume/seed'),
})

export const resumeTemplatesQuery = queryOptions({
  queryKey: ['resume-templates'],
  queryFn: () => api<ResumeTemplate[]>('/resume/templates'),
})
