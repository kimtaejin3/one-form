import { queryOptions } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { JobFeed } from './model'

export const jobsQuery = queryOptions({
  queryKey: ['jobs'],
  queryFn: () => api<JobFeed>('/jobs'),
})
