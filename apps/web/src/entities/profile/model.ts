export type ProfileData = {
  personal: {
    name: string
    name_en: string
    name_cn: string
    address: string
    phone: string
    email: string
    emergency_phone: string
    emergency_relation: string
  }
  educations: { school: string; major: string; period: string; status: string; gpa: string }[]
  languages: { language: string; test: string; score: string; date: string }[]
  awards: { title: string; org: string; date: string }[]
  certificates: { name: string; issuer: string; date: string }[]
  careers: { company: string; role: string; period: string; highlights: string[]; stack: string[] }[]
  projects: { name: string; role: string; period: string; summary: string; highlights: string[]; stack: string[] }[]
  activities: { type: string; title: string; org: string; period: string; description: string }[]
}
