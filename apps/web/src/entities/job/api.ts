import { queryOptions } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { JobDetail, JobFeed } from './model'

export type JobFilters = {
  role: string
  experience: string
  employment: string
  location: string
  page: number
}

export function jobsQuery(f: JobFilters) {
  const params = new URLSearchParams({ page: String(f.page) })
  if (f.role) params.set('role', f.role)
  if (f.experience) params.set('experience', f.experience)
  if (f.employment) params.set('employment', f.employment)
  if (f.location) params.set('location', f.location)
  return queryOptions({
    queryKey: ['jobs', f],
    queryFn: () => api<JobFeed>(`/jobs?${params.toString()}`),
  })
}

export function jobDetailQuery(id: string) {
  return queryOptions({
    queryKey: ['jobs', id],
    queryFn: () => api<JobDetail>(`/jobs/${id}`),
  })
}
