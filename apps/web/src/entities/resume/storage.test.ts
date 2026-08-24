import { beforeEach, describe, expect, test } from 'vitest'
import type { ResumeState } from './model'
import { listSavedApplications, upsertSavedApplication } from './storage'

const state = {
  doc: {
    header: { name: '김태진', contact: [], links: [] },
    personal: {
      photo: '', email: '', phone: '', address: '', birth: '', nationality: '',
      military_status: '', military_branch: '', military_period: '', veteran: '', discharge: '',
    },
    summary: '소개',
    sections: [
      { id: 'career', type: 'career', title: '경력', order: 0, visible: true, items: [] },
      { id: 'education', type: 'education', title: '학력', order: 1, visible: true, items: [] },
    ],
    essays: [{ question: '지원 동기', answer: '답변', char_limit: 700 }],
  },
  style: {
    template: 'classic', font: 'Pretendard', accent_color: '#334155',
    density: 'normal', heading_style: 'bar', font_scale: 'M',
  },
} as ResumeState

describe('입사지원서 워크스페이스 저장', () => {
  beforeEach(() => localStorage.clear())

  test('기존 단일 문서를 세 문서 워크스페이스로 읽는다', () => {
    localStorage.setItem('oneform.resumes', JSON.stringify([
      { id: 'legacy', title: '기존 이력서', state, updatedAt: 1 },
    ]))

    const application = listSavedApplications()[0]

    expect(application.included).toEqual(['resume', 'career', 'essay'])
    expect(application.documents.career.doc.sections.map((section) => section.type)).toEqual([
      'career',
    ])
    expect(application.documents.essay.doc.sections).toEqual([])
    expect(application.documents.essay.doc.essays[0].question).toBe('지원 동기')
  })

  test('세 문서와 전체 PDF 포함 선택을 함께 저장한다', () => {
    const documents = { resume: state, career: state, essay: state }
    upsertSavedApplication({
      id: 'new', title: '백엔드 지원서', documents, included: ['resume', 'essay'], updatedAt: 2,
    })

    expect(listSavedApplications()[0]).toMatchObject({
      id: 'new', title: '백엔드 지원서', included: ['resume', 'essay'],
    })
  })

  test('기존 포트폴리오 템플릿은 표준 이력서로 읽는다', () => {
    const portfolio = { ...state, style: { ...state.style, template: 'portfolio' } }
    localStorage.setItem('oneform.resumes', JSON.stringify([{
      id: 'old', title: '기존 문서', documents: {
        resume: portfolio, career: state, essay: state,
      }, included: ['resume'], updatedAt: 3,
    }]))

    expect(listSavedApplications()[0].documents.resume.style.template).toBe('classic')
  })
})
