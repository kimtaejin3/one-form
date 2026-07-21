import { useUploadResume } from '../model'

export default function UploadResume() {
  const resume = useUploadResume()

  return (
    <div className="row" style={{ marginBottom: 10 }}>
      <label className="of-btn of-btn--sm">
        {resume.isPending ? '분석 중…' : '이력서 업로드'}
        <input
          type="file"
          hidden
          accept=".pdf,.docx,.hwp"
          onChange={() => resume.mutate()}
          disabled={resume.isPending}
        />
      </label>
      {resume.data && <span className="of-mono">{resume.data.message}</span>}
    </div>
  )
}
