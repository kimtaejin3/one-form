import { queryOptions } from '@tanstack/react-query'
import { api } from '../api'

export type Application = {
  id: number
  company: string
  role: string
  channel: string
  status: string
  deadline: string
}

export const applicationsQuery = queryOptions({
  queryKey: ['applications'],
  queryFn: () => api<Application[]>('/applications'),
})
