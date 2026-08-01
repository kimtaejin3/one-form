import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { components } from '@/shared/api'

type ResumeUploadResponse = components['schemas']['ResumeUploadResponse']

export function useUploadResume() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => {
      const body = new FormData()
      body.append('file', file)
      return api<ResumeUploadResponse>('/profile/resume', { method: 'POST', body })
    },
    onSuccess: ({ profile }) => queryClient.setQueryData(['profile'], profile),
  })
}
