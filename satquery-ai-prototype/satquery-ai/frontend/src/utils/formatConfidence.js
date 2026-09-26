export const HIGH = 0.8
export const MODERATE = 0.6

export function formatConfidence(c) {
  return c == null || Number.isNaN(c) ? '—' : `${Math.round(c * 100)}%`
}

export function confidenceTier(c) {
  if (c == null) return 'insufficient'
  return c >= HIGH ? 'high' : c >= MODERATE ? 'moderate' : 'insufficient'
}

export const TIER_LABEL = { high: 'High confidence', moderate: 'Moderate — review', insufficient: 'Insufficient evidence' }
