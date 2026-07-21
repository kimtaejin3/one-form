import { queryOptions } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { ProfileData } from './model'

export const profileQuery = queryOptions({
  queryKey: ['profile'],
  queryFn: () => api<ProfileData>('/profile'),
})
