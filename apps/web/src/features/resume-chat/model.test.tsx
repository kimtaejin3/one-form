import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useResumeChat } from './model'
import * as apiModule from '@/shared/api'

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient()
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('useResumeChat', () => {
  it('반환된 state·reply를 콜백에 넘긴다', async () => {
    const fakeState = {
      doc: { header: { name: 'A', contact: [], links: [] }, summary: 'x', sections: [] },
      style: {},
    }
    vi.spyOn(apiModule, 'post').mockResolvedValue({ state: fakeState, reply: '반영했어요.' } as never)
    const onState = vi.fn()
    const { result } = renderHook(() => useResumeChat(onState), { wrapper })

    result.current.mutate({ state: fakeState as never, materials: [], message: '요약' })
    await waitFor(() => expect(onState).toHaveBeenCalledWith(fakeState, '반영했어요.'))
  })
})
