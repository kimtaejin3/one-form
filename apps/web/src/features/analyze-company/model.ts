import { useMutation } from '@tanstack/react-query'
import { post } from '@/shared/api'

export type Brief = {
  name: string
  business_areas: string[]
  products: string[]
  jd_skills: string[]
  strength_matching: { company_issue: string; my_experience: string; fit: number }[]
}

export function useAnalyzeCompany() {
  return useMutation({
    mutationFn: (name: string) => post<Brief>('/companies/analyze', { name }),
  })
}
