import { queryOptions } from '@tanstack/react-query'
import { api } from '../api'

export type Job = {
  id: number
  company: string
  domain: string
  conditions: string
  title: string
  tags: string[]
  dday: string
  source: string
  match_reason: string
}

export type JobFeed = {
  role: string
  jobs: Job[]
}

export const jobsQuery = queryOptions({
  queryKey: ['jobs'],
  queryFn: () => api<JobFeed>('/jobs'),
})
