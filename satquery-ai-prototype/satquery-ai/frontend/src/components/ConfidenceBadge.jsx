import { TIER_LABEL, confidenceTier, formatConfidence } from '../utils/formatConfidence'

const STYLE = {
  high: 'border-signal/40 bg-signal/10 text-signal',
  moderate: 'border-amber-flag/40 bg-amber-flag/10 text-amber-flag',
  insufficient: 'border-red-400/40 bg-red-400/10 text-red-300',
}

export default function ConfidenceBadge({ value, tier, compact = false }) {
  const t = tier || confidenceTier(value)
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${STYLE[t]}`} title="Model confidence — not a measured accuracy">
      <span className="font-mono">{formatConfidence(value)}</span>
      {!compact && <span className="opacity-80">{TIER_LABEL[t]}</span>}
    </span>
  )
}
