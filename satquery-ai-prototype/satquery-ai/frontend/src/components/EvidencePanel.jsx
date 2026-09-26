import { api } from '../services/api'
import { bboxLabel, formatGeo } from '../utils/coordinates'
import { formatConfidence } from '../utils/formatConfidence'
import ConfidenceBadge from './ConfidenceBadge'

const Fact = ({ label, children }) => (<div className="rounded-md border border-ink-600 bg-ink-900 p-3"><div className="mb-1 text-xs text-mist-500">{label}</div><div className="text-sm">{children}</div></div>)

function describeEvidence(ev) {
  const s = ev.stats || {}
  switch (ev.analysis_type) {
    case 'object_detection': return `${ev.count} detection${ev.count === 1 ? '' : 's'} → ${ev.count} bounding box${ev.count === 1 ? '' : 'es'}`
    case 'segmentation': return `${s.area_pct}% mask coverage${s.area_km2 != null ? ` · ${s.area_km2} km²` : ''} · ${s.regions} polygon(s)`
    case 'change_detection': return `${s.total_regions} change regions (${s.significant_regions} significant) · shown ${ev.count}`
    case 'building_change': return `${s.new} new of ${s.after_count} buildings (before ${s.before_count}) · cross-checked with change map`
    case 'image_understanding': return 'Land-cover coverage + object counts'
    default: return 'No spatial evidence was produced'
  }
}

export default function EvidencePanel({ record, highlightId, onHighlight }) {
  if (!record) return <div className="flex h-full items-center justify-center p-6 text-sm text-mist-500">Evidence appears here after you ask a question: answer, confidence, coordinates, model and visual support.</div>
  const ev = record.evidence
  const items = ev.items || []
  const mode = ev.coordinates?.mode
  const legend = record.visualization.masks?.length ? 'Segmentation mask' : record.visualization.change_mask_png ? 'Change map' : record.visualization.boxes?.length ? 'Bounding boxes' : '—'
  return (
    <div className="space-y-4 p-4">
      <section aria-label="Answer" className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1"><div className="text-xs text-mist-500">Answer</div><p className="font-display text-xl leading-snug">{record.answer}</p></div>
        <ConfidenceBadge value={record.confidence} tier={record.confidence_tier} />
      </section>
      <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
        <Fact label="Evidence">{describeEvidence(ev)}</Fact>
        <Fact label="Coordinates">{items.length ? `Available · ${mode}` : 'Not applicable'}</Fact>
        <Fact label="Model / analysis"><span className="font-mono text-xs">{ev.engine?.name}</span><div className="text-xs text-amber-flag">{record.engine_label}</div></Fact>
        <Fact label="Visual support">{legend}</Fact>
      </div>
      {record.warnings?.length > 0 && <ul className="space-y-1">{record.warnings.map((w) => <li key={w} className="rounded border border-amber-flag/30 bg-amber-flag/10 px-2 py-1 text-xs text-amber-flag">{w}</li>)}</ul>}
      {items.length > 0 && (
        <div className="max-h-56 overflow-auto rounded-md border border-ink-600">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-ink-700 text-mist-300"><tr><th className="px-2 py-1.5">ID</th><th>Label</th><th>Confidence</th><th>Location</th></tr></thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id} onClick={() => onHighlight(it.id)} className={`cursor-pointer border-t border-ink-600 hover:bg-ink-700 ${highlightId === it.id ? 'bg-signal/10' : ''}`}>
                  <td className="px-2 py-1 font-mono">{it.id}</td><td>{String(it.label).replace(/_/g, ' ')}{it.significant === false ? ' (minor)' : ''}</td>
                  <td><span className="font-mono">{formatConfidence(it.confidence)}</span></td>
                  <td className="font-mono text-mist-500">{it.geo_bbox ? formatGeo(it.geo_bbox[0]) : bboxLabel(it.bbox)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <details className="rounded-md border border-ink-600 bg-ink-900">
        <summary className="cursor-pointer px-3 py-2 text-sm font-medium">How did SatQuery AI reach this answer?</summary>
        <ol className="space-y-2 border-t border-ink-600 p-3 text-xs">
          {record.pipeline.map((s, i) => (
            <li key={i} className="flex gap-3"><span className="mt-0.5 h-1.5 w-1.5 shrink-0 translate-y-1 rounded-full bg-signal" />
              <div><div className="font-medium text-mist-100">{s.stage} <span className="font-mono font-normal text-mist-500">{s.ms} ms</span></div><div className="text-mist-300">{s.detail}</div></div></li>
          ))}
        </ol>
        <dl className="grid grid-cols-2 gap-2 border-t border-ink-600 p-3 text-xs">
          <div><dt className="text-mist-500">Intent</dt><dd>{record.intent.intent}</dd></div>
          <div><dt className="text-mist-500">Average confidence</dt><dd>{formatConfidence(record.confidence)}</dd></div>
          <div><dt className="text-mist-500">Evidence</dt><dd>{describeEvidence(ev)}</dd></div>
          <div><dt className="text-mist-500">Analysis ID</dt><dd className="font-mono">{record.id}</dd></div>
        </dl>
      </details>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-mist-500">{record.disclaimer} Confidence is the model’s own score, not measured accuracy.</p>
        <div className="flex gap-2"><a className="btn-ghost !py-1 text-xs" href={api.reportUrl(record.id)}>Download report</a>{items.length > 0 && <a className="btn-ghost !py-1 text-xs" href={api.geojsonUrl(record.id)} target="_blank" rel="noreferrer">GeoJSON</a>}</div>
      </div>
    </div>
  )
}
