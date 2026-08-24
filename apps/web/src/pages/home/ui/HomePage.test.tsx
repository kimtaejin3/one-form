import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { expect, test } from 'vitest'
import HomePage from './HomePage'

test('핵심 기능과 채용공고 추천 진입점을 제공한다', () => {
  localStorage.clear()
  render(<MemoryRouter><HomePage /></MemoryRouter>)

  expect(screen.getByRole('link', { name: '새 입사지원서' })).toHaveAttribute('href', '/resume/new')
  expect(screen.getByRole('link', { name: /^마스터 프로필/ })).toHaveAttribute('href', '/profile')
  expect(screen.getByRole('link', { name: /^양식 변환/ })).toHaveAttribute('href', '/forms')
  expect(screen.getByRole('link', { name: /추천 공고 보기/ })).toHaveAttribute('href', '/jobs')
})
