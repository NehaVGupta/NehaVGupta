import { api } from '../services/api'

/** Before / After / Change triptych (static, scaled with SVG so boxes stay aligned). */
export default function ChangeMap({ before, after, record }) {
  const viz = record?.visualization
  const regions = viz?.change_regions || []
  const highlightedBoxes = (viz?.boxes || []).filter((box) => viz?.highlight_ids?.includes(box.id))
  const W = after?.width, H = after?.height
  const Pane = ({ title, children }) => (
    <figure className="min-w-0">
      <figcaption className="mb-1 text-xs text-mist-300">{title}</figcaption>
      <div className="relative overflow-hidden rounded-md border border-ink-600" style={{ aspectRatio: `${W}/${H}` }}>{children}</div>
    </figure>
  )
  if (!before || !after) return <div className="flex h-full items-center justify-center text-sm text-mist-500">Load two images to compare.</div>
  return (
    <div className="grid h-full grid-cols-1 content-start gap-3 overflow-auto p-3 lg:grid-cols-3">
      <Pane title="Before (Image A)"><img src={api.imageUrl(before.id)} alt="Before" className="h-full w-full" /></Pane>
      <Pane title="After (Image B)"><img src={api.imageUrl(after.id)} alt="After" className="h-full w-full" /></Pane>
      <Pane title={viz?.change_mask_png ? 'Change map (significant = red, minor = amber)' : 'Change map — run “What changed?”'}>
        <img src={api.imageUrl(after.id)} alt="After with changes" className="h-full w-full opacity-60" />
        {viz?.change_mask_png && <img src={viz.change_mask_png} alt="Change mask" className="absolute inset-0 h-full w-full" />}
        <svg viewBox={`0 0 ${W} ${H}`} className="absolute inset-0 h-full w-full">
          {regions.map((r) => (
            <rect key={r.id} x={r.bbox[0]} y={r.bbox[1]} width={r.bbox[2] - r.bbox[0]} height={r.bbox[3] - r.bbox[1]} fill="none"
              stroke={r.significant ? '#ef4444' : '#fbbf24'} strokeWidth="2" strokeDasharray={r.significant ? '' : '5 4'}><title>{r.label} {Math.round(r.confidence * 100)}%</title></rect>
          ))}
          {highlightedBoxes.map((box) => (
            <rect key={box.id} x={box.bbox[0]} y={box.bbox[1]} width={box.bbox[2] - box.bbox[0]} height={box.bbox[3] - box.bbox[1]} fill="none"
              stroke="#22d3ee" strokeWidth="3"><title>{box.label} {Math.round(box.confidence * 100)}%</title></rect>
          ))}
        </svg>
      </Pane>
    </div>
  )
}
