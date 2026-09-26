import { createContext, useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import { api } from '../services/api'
import { formatGeo, pixelToGeo } from '../utils/coordinates'

export const MapCtx = createContext(null)

/** Image-space Leaflet map (CRS.Simple). Overlay components render as children and use MapCtx. */
export default function MapViewer({ image, imageB, view = 'A', children }) {
  const el = useRef()
  const base = useRef()
  const [map, setMap] = useState(null)
  const [cursor, setCursor] = useState(null)
  const shown = view === 'A' ? image : imageB || image

  useEffect(() => {
    const m = L.map(el.current, { crs: L.CRS.Simple, minZoom: -3, maxZoom: 3, zoomSnap: 0.25, attributionControl: false })
    ;[['base', 200], ['mask', 250], ['vec', 300]].forEach(([n, z]) => { m.createPane(n).style.zIndex = z })
    setMap(m)
    return () => m.remove()
  }, [])

  useEffect(() => {
    if (!map || !shown) return
    const b = [[0, 0], [shown.height, shown.width]]
    base.current?.remove()
    base.current = L.imageOverlay(api.imageUrl(shown.id), b, { pane: 'base' }).addTo(map)
    map.invalidateSize(); map.fitBounds(b, { animate: false })
    const onMove = (e) => setCursor({ x: e.latlng.lng, y: shown.height - e.latlng.lat })
    map.on('mousemove', onMove)
    return () => map.off('mousemove', onMove)
  }, [map, shown?.id])

  const geo = cursor && shown ? formatGeo(pixelToGeo(shown.geo, shown.width, shown.height, cursor.x, cursor.y)) : null
  return (
    <div className="relative h-full w-full">
      <div ref={el} className="h-full w-full" aria-label="Interactive imagery viewer" />
      {!shown && <div className="pointer-events-none absolute inset-0 flex items-center justify-center graticule text-sm text-mist-500">Upload an image or load a demo dataset to begin</div>}
      {map && shown && <MapCtx.Provider value={{ map, h: shown.height, w: shown.width, image: shown }}>{children}</MapCtx.Provider>}
      {shown && (
        <div className="pointer-events-none absolute bottom-2 left-2 z-[500] rounded bg-ink-950/80 px-2 py-1 font-mono text-[11px] text-mist-300">
          {cursor && cursor.x >= 0 && cursor.x <= shown.width && cursor.y >= 0 && cursor.y <= shown.height ? `px ${Math.round(cursor.x)}, ${Math.round(cursor.y)}${geo ? ` · ${geo}` : ''}` : 'move cursor over image'}
          {shown.synthetic && ' · synthetic demo image'}
        </div>
      )}
    </div>
  )
}
