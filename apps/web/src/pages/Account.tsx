import { Card } from '@one-form/design-system'

export default function Account() {
  return (
    <div className="stack" style={{ maxWidth: 480 }}>
      <Card>
        <div className="stack">
          <div className="row">
            <div className="avatar avatar--lg">
              <svg viewBox="0 0 24 24" width="30" height="30" aria-hidden="true">
                <path
                  d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
                  fill="currentColor"
                />
              </svg>
            </div>
            <div className="stack" style={{ gap: 4 }}>
              <strong>김지원</strong>
              <span className="of-chip">무료 플랜</span>
            </div>
          </div>
          <button className="of-btn" style={{ width: '100%' }}>
            프로로 업그레이드 →
          </button>
        </div>
      </Card>
      <Card>
        <dl className="info-grid">
          <dt>이메일</dt>
          <dd>jiwon@example.com</dd>
          <dt>가입일</dt>
          <dd>2026.03.14</dd>
          <dt>지원 기업</dt>
          <dd>5곳</dd>
        </dl>
      </Card>
      <button className="of-btn of-btn--ghost" style={{ alignSelf: 'flex-start' }}>
        로그아웃
      </button>
    </div>
  )
}
