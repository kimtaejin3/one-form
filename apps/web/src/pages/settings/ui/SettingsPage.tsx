import { Card } from '@one-form/design-system'

export default function SettingsPage() {
  return (
    <div className="stack" style={{ maxWidth: 480 }}>
      <Card>
        <div className="stack">
          <strong>알림</strong>
          <label className="setting-row">
            <span>마감 리마인더</span>
            <input type="checkbox" defaultChecked />
          </label>
          <label className="setting-row">
            <span>새 공고 추천 알림</span>
            <input type="checkbox" defaultChecked />
          </label>
          <label className="setting-row">
            <span>이메일 수신</span>
            <input type="checkbox" />
          </label>
        </div>
      </Card>
      <Card>
        <div className="stack">
          <strong>일반</strong>
          <label className="setting-row">
            <span>언어</span>
            <select defaultValue="ko">
              <option value="ko">한국어</option>
              <option value="en">English</option>
            </select>
          </label>
          <label className="setting-row">
            <span>공개 프로필</span>
            <input type="checkbox" />
          </label>
        </div>
      </Card>
    </div>
  )
}
