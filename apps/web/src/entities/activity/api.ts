import { queryOptions } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { Activity } from './model'

export const activitiesQuery = queryOptions({
  queryKey: ['activities'],
  queryFn: () => api<Activity[]>('/activities'),
})
