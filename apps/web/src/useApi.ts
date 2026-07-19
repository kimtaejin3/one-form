import { useEffect, useState } from 'react'
import { api } from './api'

export function useApi<T>(path: string) {
  const [data, setData] = useState<T | null>(null)
  useEffect(() => {
    let alive = true
    api<T>(path)
      .then((d) => {
        if (alive) setData(d)
      })
      .catch(console.error)
    return () => {
      alive = false
    }
  }, [path])
  return data
}
