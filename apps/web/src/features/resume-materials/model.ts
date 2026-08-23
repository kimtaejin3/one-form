import { useMutation } from '@tanstack/react-query'
import type { ResumeMaterial } from '@/entities/resume'

// 업로드는 multipart라 JSON 헬퍼 대신 fetch(FormData). Vite가 /api를 프록시.
export function useExtractMaterial(onText: (m: ResumeMaterial) => void) {
  return useMutation({
    mutationFn: async (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch('/api/resume/materials/extract', { method: 'POST', body: fd })
      if (!res.ok) throw new Error('extract failed')
      return (await res.json()) as { text: string }
    },
    onSuccess: (res, file) => onText({ kind: 'file', label: file.name, text: res.text }),
  })
}
