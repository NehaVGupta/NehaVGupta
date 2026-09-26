import { formatGeo } from '../utils/coordinates'

export default function MetadataPanel({ image, title = 'Image metadata' }) {
  if (!image) return null
  const g = image.geo || {}
  const rows = [
    ['Format', `${image.format} · ${(image.size_bytes / 1024).toFixed(0)} KB`],
    ['Dimensions', `${image.width} × ${image.height} px${image.scale > 1 ? ` (from ${image.orig_width}×${image.orig_height})` : ''}`],
    ['Georeferenced', g.georeferenced ? (g.illustrative ? 'Illustrative (synthetic)' : 'Yes') : 'No — pixel coordinates'],
    g.crs && ['CRS', g.crs],
    g.bounds && ['Bounds', `${formatGeo([g.bounds[0], g.bounds[3]])} → ${formatGeo([g.bounds[2], g.bounds[1]])}`],
    g.gsd_m && ['Resolution', `${g.gsd_m} m/px${g.illustrative ? ' (illustrative)' : ''}`],
    g.bands && ['Bands', g.bands],
    ['Quality score', `${Math.round((image.quality?.score ?? 0) * 100)}%`],
  ].filter(Boolean)
  return (
    <div className="space-y-2">
      <div className="text-sm font-medium">{title}</div>
      <dl className="space-y-1 text-xs">
        {rows.map(([k, v]) => (<div key={k} className="flex justify-between gap-3"><dt className="text-mist-500">{k}</dt><dd className="text-right font-mono text-mist-300">{v}</dd></div>))}
      </dl>
      {image.quality?.warnings?.map((w) => <p key={w} className="rounded border border-amber-flag/30 bg-amber-flag/10 px-2 py-1 text-xs text-amber-flag">{w}</p>)}
      {g.note && <p className="text-xs text-mist-500">{g.note}</p>}
    </div>
  )
}
