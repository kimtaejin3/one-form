import { describe, expect, it, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeToggle } from './ThemeToggle'

beforeEach(() => {
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
})

describe('ThemeToggle', () => {
  it('저장된 테마가 없으면 OS 설정(jsdom=light)을 따르고, 클릭하면 dark로 전환·저장한다', () => {
    render(<ThemeToggle />)
    fireEvent.click(screen.getByRole('button'))

    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(localStorage.theme).toBe('dark')
  })

  it('dark 상태에서 클릭하면 light로 돌아온다', () => {
    document.documentElement.dataset.theme = 'dark'
    render(<ThemeToggle />)
    fireEvent.click(screen.getByRole('button'))

    expect(document.documentElement.dataset.theme).toBe('light')
    expect(localStorage.theme).toBe('light')
  })
})
