import { Suspense, type ReactNode } from 'react'
import { QueryErrorResetBoundary } from '@tanstack/react-query'
import { ErrorBoundary } from 'react-error-boundary'
import Loading from './Loading'

/**
 * 자식의 비동기 상태를 대신 처리한다.
 * - 로딩: Suspense fallback (Loading)
 * - 에러: ErrorBoundary + QueryErrorResetBoundary로 재시도
 * 덕분에 페이지 컴포넌트는 데이터가 항상 준비된 상태만 다룬다.
 */
export default function AsyncBoundary({ children }: { children: ReactNode }) {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ resetErrorBoundary }) => (
            <div className="error-view">
              <p>데이터를 불러오지 못했습니다.</p>
              <button className="of-btn of-btn--sm" onClick={resetErrorBoundary}>
                다시 시도
              </button>
            </div>
          )}
        >
          <Suspense fallback={<Loading />}>{children}</Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  )
}
