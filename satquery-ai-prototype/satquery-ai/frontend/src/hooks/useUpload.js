import { useCallback, useState } from 'react'
import { api } from '../services/api'

const MAX_MB = 50

export function useUpload() {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

  const upload = useCallback(async (file) => {
    setError(null)
    if (!file) return null
    if (file.size > MAX_MB * 1024 * 1024) { setError(`File is too large (limit ${MAX_MB} MB).`); return null }
    if (!/\.(png|jpe?g|tiff?)$/i.test(file.name)) { setError('Unsupported file type. Please upload PNG, JPG or GeoTIFF.'); return null }
    setUploading(true)
    try { return await api.upload(file) } catch (e) { setError(e.message); return null } finally { setUploading(false) }
  }, [])

  return { upload, uploading, error, clearError: () => setError(null) }
}
