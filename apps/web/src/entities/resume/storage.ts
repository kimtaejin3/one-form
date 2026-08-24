import type {
  ResumeApplicationDocuments,
  ResumeDocumentKind,
  ResumeState,
} from './model'

export interface SavedApplication {
  id: string
  title: string
  documents: ResumeApplicationDocuments
  included: ResumeDocumentKind[]
  updatedAt: number
}

interface LegacySavedDoc {
  id: string
  title: string
  state: ResumeState
  updatedAt: number
}

const KEY = 'oneform.resumes'
const ALL_DOCUMENTS: ResumeDocumentKind[] = ['resume', 'career', 'essay']

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

function migrate(doc: LegacySavedDoc): SavedApplication {
  const resume = clone(doc.state)
  if (resume.style.template === 'portfolio') resume.style.template = 'classic'
  const career = clone(doc.state)
  career.doc.summary = ''
  career.doc.essays = []
  career.doc.sections = career.doc.sections.filter(
    (section) => section.type === 'career' || section.type === 'project',
  )
  const essay = clone(doc.state)
  essay.doc.summary = ''
  essay.doc.sections = []

  return {
    id: doc.id,
    title: doc.title,
    documents: { resume, career, essay },
    included: ALL_DOCUMENTS,
    updatedAt: doc.updatedAt,
  }
}

function normalize(application: SavedApplication): SavedApplication {
  if (application.documents.resume.style.template !== 'portfolio') return application
  const next = clone(application)
  next.documents.resume.style.template = 'classic'
  return next
}

export function listSavedApplications(): SavedApplication[] {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return []
    return (JSON.parse(raw) as Array<SavedApplication | LegacySavedDoc>).map((item) =>
      normalize('documents' in item ? item : migrate(item)),
    )
  } catch {
    return []
  }
}

export function getSavedApplication(id: string): SavedApplication | undefined {
  return listSavedApplications().find((application) => application.id === id)
}

export function upsertSavedApplication(application: SavedApplication): void {
  const rest = listSavedApplications().filter((item) => item.id !== application.id)
  try {
    localStorage.setItem(KEY, JSON.stringify([application, ...rest]))
  } catch {
    // 저장 공간 부족이어도 편집·PDF 다운로드는 계속 사용할 수 있다.
  }
}

export function removeSavedApplication(id: string): void {
  const next = listSavedApplications().filter((application) => application.id !== id)
  try {
    localStorage.setItem(KEY, JSON.stringify(next))
  } catch {
    /* noop */
  }
}

export function newApplicationId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}
