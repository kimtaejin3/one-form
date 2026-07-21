import { useMutation } from '@tanstack/react-query'
import { post } from '@/shared/api'

export type ConvertResult = {
  form_name: string
  mappings: { form_field: string; profile_field: string; confidence: number }[]
}

export function useConvertForm() {
  return useMutation({ mutationFn: () => post<ConvertResult>('/forms/convert') })
}
