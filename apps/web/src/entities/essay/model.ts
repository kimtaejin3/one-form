import type { components } from '@/shared/api'

export type Question = components['schemas']['Question']
export type AnswerSlot = components['schemas']['AnswerSlot']

/** 어떤 기업도 쓰지 않는 문항의 슬롯 회사명(백엔드와 같은 문자열). */
export const COMMON = '공통'

/** 답변은 (기업 × 문항)마다 별개라 편집 중 본문도 이 키로 보관한다. */
export function slotKey(questionId: number, company: string) {
  return `${questionId}:${company}`
}
