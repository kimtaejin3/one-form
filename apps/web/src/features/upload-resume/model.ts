import { useMutation } from '@tanstack/react-query'
import { post } from '@/shared/api'

export function useUploadResume() {
  return useMutation({ mutationFn: () => post<{ message: string }>('/profile/resume') })
}
