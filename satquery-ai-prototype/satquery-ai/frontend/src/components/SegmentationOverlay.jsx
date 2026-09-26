import { useContext, useEffect } from 'react'
import L from 'leaflet'
import { MapCtx } from './MapViewer'
import { toLatLng } from '../utils/coordinates'

/** Raster mask(s) plus vector outlines for a segmentation result. */
export default function SegmentationOverlay({ masks = [], polygons = [], opacity = 0.85, highlightIds = [], focusId, onSelect }) {
  const { map, h, w } = useContext(MapCtx)
  useEffect(() => {
    const g = L.layerGroup().addTo(map)
    masks.forEach((m) => g.addLayer(L.imageOverlay(m.mask_png, [[0, 0], [h, w]], { pane: 'mask', opacity })))
    polygons.forEach((p) => {
      const on = highlightIds.includes(p.id) || focusId === p.id
      const poly = L.polygon(p.points.map((pt) => toLatLng(pt, h)), { pane: 'vec', color: on ? '#fde047' : '#e8eef8', weight: on ? 3 : 1, fillOpacity: 0, opacity: on ? 1 : 0.55 })
      poly.bindTooltip(`${p.label} region ${p.id}`, { sticky: true })
      poly.on('click', () => onSelect?.(p.id))
      g.addLayer(poly)
    })
    return () => g.remove()
  }, [map, h, w, masks, polygons, opacity, highlightIds.join(','), focusId])
  return null
}
