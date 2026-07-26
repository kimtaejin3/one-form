import { useState } from 'react'
import { Icon } from './Icon'

/** 초기값: index.html이 복원한 data-theme → 없으면 OS 설정 */
function currentTheme() {
  return (
    document.documentElement.dataset.theme ||
    // ?. — jsdom엔 matchMedia가 없다 (테스트에선 light)
    (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
  )
}

export function ThemeToggle() {
  const [theme, setTheme] = useState(currentTheme)
  const next = theme === 'dark' ? 'light' : 'dark'

  return (
    <button
      type="button"
      className="icon-btn"
      title={next === 'dark' ? '다크 모드' : '라이트 모드'}
      aria-label={next === 'dark' ? '다크 모드로 전환' : '라이트 모드로 전환'}
      onClick={() => {
        document.documentElement.dataset.theme = next
        localStorage.theme = next
        setTheme(next)
      }}
    >
      <Icon name={theme === 'dark' ? 'dark-mode' : 'light-mode'} />
    </button>
  )
}
