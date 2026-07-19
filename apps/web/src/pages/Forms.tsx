import { useState } from 'react'
import { Card } from '@one-form/design-system'
import { post } from '../api'

type ConvertResult = {
  form_name: string
  mappings: { form_field: string; profile_field: string; confidence: number }[]
}

export default function Forms() {
  const [result, setResult] = useState<ConvertResult | null>(null)
  const [converting, setConverting] = useState(false)

  async function onUpload() {
    setConverting(true)
    setResult(await post<ConvertResult>('/forms/convert'))
    setConverting(false)
  }

  return (
    <>
      <h2 className="of-h2">양식 변환</h2>
      <p className="page-desc">자사 양식(DOCX·HWP)을 업로드하면 마스터 프로필 필드와 자동 매핑합니다.</p>
      <div className="row" style={{ marginBottom: 28 }}>
        <label className="of-btn of-btn--sm">
          {converting ? '매핑 중…' : '양식 업로드'}
          <input type="file" hidden accept=".docx,.xlsx,.hwp" onChange={onUpload} disabled={converting} />
        </label>
      </div>
      {result && (
        <Card>
          <strong>{result.form_name} — 매핑 시뮬레이션</strong>
          <table className="data-table" style={{ marginTop: 12 }}>
            <thead>
              <tr>
                <th>양식 필드</th>
                <th>프로필 필드</th>
                <th>신뢰도</th>
              </tr>
            </thead>
            <tbody>
              {result.mappings.map((m) => (
                <tr key={m.form_field}>
                  <td>{m.form_field}</td>
                  <td>{m.profile_field}</td>
                  <td>
                    <span className="of-chip">{m.confidence}%</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </>
  )
}
