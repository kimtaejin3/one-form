import { useMutation, useQueryClient } from '@tanstack/react-query'
import { put } from '@/shared/api'
import type { ProfileData } from '@/entities/profile'

export function useSaveProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (profile: ProfileData) => put<ProfileData>('/profile', profile),
    onSuccess: (profile) => queryClient.setQueryData(['profile'], profile),
  })
}
