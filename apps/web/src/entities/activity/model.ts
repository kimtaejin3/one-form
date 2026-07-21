export type Activity = {
  id: number
  name: string
  category: string
  period: string
  fit: number
  fills_gap: string[]
  expected_experience: string
  connections: { company: string; role: string }[]
}
