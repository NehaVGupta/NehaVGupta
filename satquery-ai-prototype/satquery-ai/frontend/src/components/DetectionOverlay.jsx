import { useContext, useEffect } from 'react'
import L from 'leaflet'
import { MapCtx } from './MapViewer'
import { bboxLabel, bboxToBounds, formatGeo } from '../utils/coordinates'
import { formatConfidence } from '../utils/formatConfidence'

export const CLASS_COLOR = { building: '#f59e0b', vehicle: '#e879f9', ship: '#38bdf8', agricultural_structure: '#a3e635', 'new building': '#f43f5e' }
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))

/** Bounding boxes with click-to-inspect popups. */
export default function DetectionOverlay({ boxes, itemsById = {}, highlightIds = [], focusId, onSelect }) {
  const { map, h } = useContext(MapCtx)
  useEffect(() => {
    const g = L.layerGroup().addTo(map)
    const hl = new Set(highlightIds)
    boxes.forEach((b) => {
      const on = hl.has(b.id) || focusId === b.id
      const dim = hl.size > 0 && !on
      const color = on ? '#fde047' : CLASS_COLOR[b.label] || '#f59e0b'
      const r = L.rectangle(bboxToBounds(b.bbox, h), { pane: 'vec', color, weight: on ? 3 : 1.6, fillColor: color, fillOpacity: on ? 0.25 : 0.06, opacity: dim ? 0.35 : 1 })
      const geo = itemsById[b.id]?.geo_bbox
      r.bindTooltip(`${esc(b.label)} · ${formatConfidence(b.confidence)}`, { sticky: true })
      r.bindPopup(`<b>Object:</b> ${esc(b.label)}<br/><b>Confidence:</b> ${formatConfidence(b.confidence)}<br/><b>Coordinates:</b> ${esc(bboxLabel(b.bbox))}${geo ? `<br/>${esc(formatGeo(geo[0]))}` : ''}`)
      r.on('click', () => onSelect?.(b.id))
      g.addLayer(r)
      if (focusId === b.id) map.panTo(r.getBounds().getCenter())
    })
    return () => g.remove()
  }, [map, h, boxes, highlightIds.join(','), focusId])
  return null
}
