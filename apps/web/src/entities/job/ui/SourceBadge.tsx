import { useState } from 'react'

// 채용 출처 → 도메인 (favicon 로고용). 자사 채용은 외부 사이트가 없어 로고 없이 텍스트만.
const SOURCE_DOMAIN: Record<string, string> = {
  원티드: 'wanted.co.kr',
  잡코리아: 'jobkorea.co.kr',
  사람인: 'saramin.co.kr',
  링크드인: 'linkedin.com',
}

export default function SourceBadge({ source }: { source: string }) {
  const domain = SOURCE_DOMAIN[source]
  const [failed, setFailed] = useState(false)

  return (
    <span className="job-badge job-source">
      {domain && !failed && (
        <img
          src={`https://www.google.com/s2/favicons?domain=${domain}&sz=64`}
          alt=""
          width={14}
          height={14}
          onError={() => setFailed(true)}
        />
      )}
      {source}
    </span>
  )
}
