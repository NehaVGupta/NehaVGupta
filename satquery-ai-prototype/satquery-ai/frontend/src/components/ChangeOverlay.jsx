import { useContext, useEffect } from 'react'
import L from 'leaflet'
import { MapCtx } from './MapViewer'
import { bboxLabel, bboxToBounds } from '../utils/coordinates'
import { formatConfidence } from '../utils/formatConfidence'

/** Change mask + per-region rectangles (red = significant, amber = minor). */
export default function ChangeOverlay({ maskPng, regions = [], opacity = 0.85, highlightIds = [], focusId, onSelect }) {
  const { map, h, w } = useContext(MapCtx)
  useEffect(() => {
    const g = L.layerGroup().addTo(map)
    if (maskPng) g.addLayer(L.imageOverlay(maskPng, [[0, 0], [h, w]], { pane: 'mask', opacity }))
    const hl = new Set(highlightIds)
    regions.forEach((r) => {
      const on = hl.has(r.id) || focusId === r.id
      const color = on ? '#fde047' : r.significant ? '#ef4444' : '#fbbf24'
      const rect = L.rectangle(bboxToBounds(r.bbox, h), { pane: 'vec', color, weight: on ? 3 : 1.4, dashArray: r.significant ? null : '4 3', fillOpacity: on ? 0.2 : 0, opacity: hl.size && !on ? 0.4 : 1 })
      rect.bindTooltip(`${r.label.replace(/_/g, ' ')} · ${formatConfidence(r.confidence)}`, { sticky: true })
      rect.bindPopup(`<b>${r.id}</b> — ${r.label.replace(/_/g, ' ')}<br/>${r.significant ? 'Significant' : 'Minor'} · ${formatConfidence(r.confidence)}<br/>${bboxLabel(r.bbox)}`)
      rect.on('click', () => onSelect?.(r.id))
      g.addLayer(rect)
      if (focusId === r.id) map.panTo(rect.getBounds().getCenter())
    })
    return () => g.remove()
  }, [map, h, w, maskPng, regions, opacity, highlightIds.join(','), focusId])
  return null
}
