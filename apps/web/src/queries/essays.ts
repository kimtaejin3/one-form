import { queryOptions } from '@tanstack/react-query'
import { api } from '../api'

export type Essay = {
  id: number
  company: string
  question: string
  char_limit: number
  deadline: string
  status: string
}

export const essaysQuery = queryOptions({
  queryKey: ['essays'],
  queryFn: () => api<Essay[]>('/essays'),
})
