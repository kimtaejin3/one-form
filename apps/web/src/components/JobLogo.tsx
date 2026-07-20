import { useState } from 'react'

/** 도메인 기반 로고(구글 favicon). 없거나 실패하면 회사명 이니셜로 폴백. */
export default function JobLogo({ company, domain }: { company: string; domain: string }) {
  const [failed, setFailed] = useState(false)

  if (failed || !domain) {
    return <div className="job-logo">{company.slice(0, 2)}</div>
  }
  return (
    <div className="job-logo">
      <img
        src={`https://www.google.com/s2/favicons?domain=${domain}&sz=128`}
        alt={company}
        width={28}
        height={28}
        onError={() => setFailed(true)}
      />
    </div>
  )
}
