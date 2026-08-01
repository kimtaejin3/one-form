import { useUploadResume } from '../model'

type Props = { onUploaded?: () => void }

export default function UploadResume({ onUploaded }: Props) {
  const resume = useUploadResume()

  return (
    <div className="row" style={{ marginBottom: 10 }}>
      <label className="of-btn of-btn--sm">
        {resume.isPending ? '분석 중…' : '이력서 업로드'}
        <input
          type="file"
          hidden
          accept="application/pdf,.pdf"
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) resume.mutate(file, { onSuccess: () => onUploaded?.() })
            event.currentTarget.value = ''
          }}
          disabled={resume.isPending}
        />
      </label>
      {resume.data && <span className="of-mono">{resume.data.message}</span>}
      {resume.error && <span className="form-error">PDF 업로드에 실패했습니다. 파일을 확인해 주세요.</span>}
    </div>
  )
}
