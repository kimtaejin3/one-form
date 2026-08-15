import { useMutation, useQuery } from '@tanstack/react-query'
import { api, post, type components } from '@/shared/api'

export type Intelligence = components['schemas']['CompanyIntelligence']
export type Source = components['schemas']['SourceSummary']
export type Signal = components['schemas']['IntelligenceSignal']
export type SourcedText = components['schemas']['SourcedText']
export type CompanyJob = components['schemas']['CompanyJob']
export type CompanyMatch = components['schemas']['CompanyMatch']

export type AnalyzeInput = {
  name: string
  job_url?: string
  force_refresh?: boolean
}

export function useAnalyzeCompany() {
  return useMutation({
    // 분석 중에도 이전 결과를 유지한다 — data는 다음 성공까지 남는다(계획서 §8).
    mutationFn: (input: AnalyzeInput) => post<Intelligence>('/companies/analyze', input),
  })
}

/** 매칭은 서버가 조회 시점 프로필로 계산한다 — 분석 결과에 굳어 있지 않다. */
export function useCompanyMatches(normalizedName: string | undefined, jobId: number | undefined) {
  return useQuery({
    queryKey: ['company-matches', normalizedName, jobId],
    enabled: Boolean(normalizedName && jobId),
    queryFn: () =>
      api<CompanyMatch[]>(
        `/companies/${encodeURIComponent(normalizedName!)}/matches?job_id=${jobId}`,
      ),
  })
}
