import { queryOptions } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { Essay } from './model'

export const essaysQuery = queryOptions({
  queryKey: ['essays'],
  queryFn: () => api<Essay[]>('/essays'),
})
