import type { components } from '@/shared/api'

export type Question = components['schemas']['Question']
export type QuestionCompany = components['schemas']['QuestionCompany']

/**
 * 질문·답변은 원본(`{회사}` 토큰 포함)으로 저장하고, 표시할 때만 지금 맥락의 회사명으로 바꾼다.
 * 기업 맥락이 없으면(문항별 뷰) `귀사`.
 */
export function fillCompany(text: string, company?: string) {
  return text.replaceAll('{회사}', company || '귀사')
}
