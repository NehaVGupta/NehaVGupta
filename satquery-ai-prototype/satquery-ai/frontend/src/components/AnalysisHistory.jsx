import { Link } from 'react-router-dom'
import ConfidenceBadge from './ConfidenceBadge'

export default function AnalysisHistory({ items }) {
  if (!items?.length) return <p className="p-4 text-sm text-mist-500">No analyses yet — start Demo Mode to create some.</p>
  return (
    <ul className="divide-y divide-ink-600">
      {items.map((h) => (
        <li key={h.id}>
          <Link to={`/analysis?open=${h.id}`} className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-ink-700">
            <div className="min-w-0"><div className="truncate text-sm">{h.query}</div><div className="truncate text-xs text-mist-500">{h.intent.replace(/_/g, ' ')} · {new Date(h.created).toLocaleString()} · {h.is_demo ? 'prototype inference' : 'model'}</div></div>
            {h.confidence != null ? <ConfidenceBadge value={h.confidence} compact /> : <span className="chip">n/a</span>}
          </Link>
        </li>
      ))}
    </ul>
  )
}
