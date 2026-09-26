import { useCallback, useState } from 'react'
import { api } from '../services/api'

export function useQuery() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const ask = useCallback(async (body) => {
    setLoading(true); setError(null)
    try { return await api.query(body) } catch (e) { setError(e.message); return null } finally { setLoading(false) }
  }, [])

  return { ask, loading, error, clearError: () => setError(null) }
}
