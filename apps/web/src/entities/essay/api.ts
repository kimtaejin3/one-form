import { queryOptions } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { Question } from './model'

// 문항 풀 한 방으로 두 뷰(문항별·기업별)를 모두 파생한다 — 회사별 요청을 따로 두지 않는다.
export const questionsQuery = queryOptions({
  queryKey: ['essay-questions'],
  queryFn: () => api<Question[]>('/essays/questions'),
})
