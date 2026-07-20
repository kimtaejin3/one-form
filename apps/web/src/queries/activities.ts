import { queryOptions } from '@tanstack/react-query'
import { api } from '../api'

export type Activity = {
  id: number
  name: string
  category: string
  period: string
  fit: number
  fills_gap: string[]
  expected_experience: string
  connections: { company: string; role: string }[]
}

export const activitiesQuery = queryOptions({
  queryKey: ['activities'],
  queryFn: () => api<Activity[]>('/activities'),
})
