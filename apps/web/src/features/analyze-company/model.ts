import { useMutation } from '@tanstack/react-query'
import { post, type components } from '@/shared/api'

export type Brief = components['schemas']['CompanyBrief']

export function useAnalyzeCompany() {
  return useMutation({
    mutationFn: (name: string) => post<Brief>('/companies/analyze', { name }),
  })
}
