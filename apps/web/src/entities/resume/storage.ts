import type { ResumeState } from './model'

// 저장된 이력서/포트폴리오 — 개인 도구라 localStorage에 보관(브라우저별). 나중에 서버로 교체 가능.
export interface SavedDoc {
  id: string
  title: string
  kind: string // resume | portfolio
  template: string // 표시용 템플릿 id
  state: ResumeState
  updatedAt: number
}

const KEY = 'oneform.resumes'

export function listSavedDocs(): SavedDoc[] {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as SavedDoc[]) : []
  } catch {
    return []
  }
}

export function getSavedDoc(id: string): SavedDoc | undefined {
  return listSavedDocs().find((d) => d.id === id)
}

export function upsertSavedDoc(doc: SavedDoc): void {
  const rest = listSavedDocs().filter((d) => d.id !== doc.id)
  const next = [doc, ...rest]
  try {
    localStorage.setItem(KEY, JSON.stringify(next))
  } catch {
    // 저장 실패(용량 등)는 조용히 무시 — 미리보기/다운로드는 그대로 동작.
  }
}

export function removeSavedDoc(id: string): void {
  const next = listSavedDocs().filter((d) => d.id !== id)
  try {
    localStorage.setItem(KEY, JSON.stringify(next))
  } catch {
    /* noop */
  }
}

export function newDocId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}
