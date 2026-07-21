export type Job = {
  id: number
  company: string
  domain: string
  conditions: string
  title: string
  tags: string[]
  dday: string
  source: string
  match_reason: string
}

export type JobFeed = {
  role: string
  total: number
  page: number
  size: number
  jobs: Job[]
}
