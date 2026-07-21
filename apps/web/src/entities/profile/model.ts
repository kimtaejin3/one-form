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
  educations: { school: string; period: string; status: string; note: string }[]
  languages: { name: string; test: string; score: string }[]
  awards: { title: string; org: string; date: string }[]
  certificates: string[]
  career: { type: string; title: string; org: string; period: string; description: string }[]
}
