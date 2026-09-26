const BASE = import.meta.env.VITE_API_URL || ''

export class ApiError extends Error {
  constructor(code, message) { super(message); this.code = code }
}

async function request(path, opts = {}) {
  let res
  try {
    res = await fetch(`${BASE}/api${path}`, opts)
  } catch {
    throw new ApiError('backend_unavailable', 'Cannot reach the SatQuery backend. Check that it is running (uvicorn app.main:app --port 8000).')
  }
  const isJson = (res.headers.get('content-type') || '').includes('json')
  const body = isJson ? await res.json() : null
  if (!res.ok) throw new ApiError(body?.error?.code || 'error', body?.error?.message || 'Something went wrong. Please try again.')
  return body
}

const post = (path, data) => request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })

export const api = {
  health: () => request('/health'),
  upload(file) { const f = new FormData(); f.append('file', file); return request('/upload', { method: 'POST', body: f }) },
  demoDatasets: () => request('/demo/datasets'),
  demoLoad: (name) => request(`/demo/load/${name}`, { method: 'POST' }),
  query: (body) => post('/query', body),
  analyze: (kind, body) => post(`/analyze/${kind}`, body),
  analysis: (id) => request(`/analysis/${id}`),
  imageMeta: (id) => request(`/image/${id}/meta`),
  history: () => request('/history'),
  stats: () => request('/stats'),
  models: () => request('/models'),
  imageUrl: (id) => `${BASE}/api/image/${id}`,
  reportUrl: (id) => `${BASE}/api/report/${id}`,
  geojsonUrl: (id) => `${BASE}/api/analysis/${id}/geojson`,
}
