const BASE = import.meta.env.VITE_API_URL || ''

export class ApiError extends Error {
  constructor(code, message) { super(message); this.code = code }
}

async function request(path, opts = {}) {
  let res
  const headers = new Headers(opts.headers || {})
  const csrf = document.cookie.split('; ').find((part) => part.startsWith('satquery_csrf='))?.split('=').slice(1).join('=')
  if (csrf && opts.method && opts.method !== 'GET') headers.set('X-CSRF-Token', decodeURIComponent(csrf))
  try {
    res = await fetch(`${BASE}/api${path}`, { ...opts, headers, credentials: 'include' })
  } catch {
    throw new ApiError('backend_unavailable', 'Cannot reach the SatQuery backend. Check that it is running (uvicorn app.main:app --port 8000).')
  }
  const isJson = (res.headers.get('content-type') || '').includes('json')
  const body = isJson ? await res.json() : null
  if (res.status === 401) window.dispatchEvent(new Event('satquery:unauthorized'))
  if (!res.ok) throw new ApiError(body?.error?.code || 'error', body?.error?.message || 'Something went wrong. Please try again.')
  return body
}

const post = (path, data) => request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })

export const api = {
  health: () => request('/health'),
  authMe: () => request('/auth/me'),
  login: (data) => post('/auth/login', data),
  register: (data) => post('/auth/register', data),
  logout: () => post('/auth/logout', {}),
  forgotPassword: (data) => post('/auth/forgot-password', data),
  resetPassword: (data) => post('/auth/reset-password', data),
  upload(file) { const f = new FormData(); f.append('file', file); return request('/upload', { method: 'POST', body: f }) },
  demoDatasets: () => request('/demo/datasets'),
  demoLoad: (name) => request(`/demo/load/${name}`, { method: 'POST' }),
  query: (body) => post('/query', body),
  analyze: (kind, body) => post(`/analyze/${kind}`, body),
  analysis: (id) => request(`/analysis/${id}`),
  imageMeta: (id) => request(`/image/${id}/meta`),
  history: (includeDemo = true) => request(`/history?include_demo=${includeDemo}`),
  stats: (includeDemo = true) => request(`/stats?include_demo=${includeDemo}`),
  models: () => request('/models'),
  imageUrl: (id) => `${BASE}/api/image/${id}`,
  reportUrl: (id) => `${BASE}/api/report/${id}`,
  geojsonUrl: (id) => `${BASE}/api/analysis/${id}/geojson`,
}
