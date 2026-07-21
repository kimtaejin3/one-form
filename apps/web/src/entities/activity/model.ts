export type Activity = {
  id: number
  name: string
  category: string
  organizer: string
  period: string
  dday: string
  fit: number
  fills_gap: string[]
  expected_experience: string
  connections: { company: string; role: string }[]
}
