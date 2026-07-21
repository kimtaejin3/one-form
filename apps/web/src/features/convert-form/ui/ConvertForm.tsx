import { Card } from '@one-form/design-system'
import { Dropzone } from '@/shared/ui'
import { useConvertForm } from '../model'

export default function ConvertForm() {
  const convert = useConvertForm()
  const result = convert.data

  return (
    <div className="stack">
      <Dropzone
        title="기업 양식 파일을 올려보세요"
        desc="HWP · DOCX · XLSX · 웹 서식 URL 지원 — 마스터 프로필로 자동 완성됩니다."
        accept=".docx,.xlsx,.hwp"
        buttonLabel="파일 선택"
        busy={convert.isPending}
        busyLabel="매핑 중…"
        onFile={() => convert.mutate()}
      />
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
    </div>
  )
}
