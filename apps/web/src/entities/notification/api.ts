import { queryOptions } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { Notification } from './model'

export const notificationsQuery = queryOptions({
  queryKey: ['notifications'],
  queryFn: () => api<Notification[]>('/notifications'),
})
