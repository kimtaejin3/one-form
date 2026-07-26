import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { expect, test } from 'vitest'
import type { Job } from '../model'
import JobCard from './JobCard'

const job: Job = {
  id: 1,
  company: '네이버',
  domain: 'navercorp.com',
  conditions: '신입 · 정규직 · 서울',
  title: '[네이버] 백엔드 개발자',
  tags: ['Java'],
  dday: 'D-3',
  source: '자사 채용',
  match_rate: 87,
  match_reason: '잘 맞아요',
}

function renderCard() {
  render(
    <MemoryRouter>
      <JobCard job={job} />
    </MemoryRouter>,
  )
}

test('매칭률과 매칭 근거를 함께 보여준다', () => {
  renderCard()

  expect(screen.getByText('87% 매칭')).toBeTruthy()
  expect(screen.getByText('잘 맞아요')).toBeTruthy()
})

test('제목이 상세 페이지(/jobs/:id)로 링크된다', () => {
  renderCard()

  expect(screen.getByRole('link', { name: '[네이버] 백엔드 개발자' }).getAttribute('href')).toBe(
    '/jobs/1',
  )
})
