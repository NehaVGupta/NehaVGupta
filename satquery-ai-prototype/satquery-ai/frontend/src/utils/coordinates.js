// Leaflet CRS.Simple uses [lat, lng] = [y_up, x]; image pixels use y down.
export const toLatLng = ([x, y], h) => [h - y, x]
export const bboxToBounds = ([x1, y1, x2, y2], h) => [[h - y2, x1], [h - y1, x2]]

export function pixelToGeo(geo, w, h, x, y) {
  if (!geo || !geo.bounds) return null
  const [l, b, r, t] = geo.bounds
  return [l + (x / w) * (r - l), t - (y / h) * (t - b)]
}

export function formatGeo(p) {
  return p ? `${p[1].toFixed(5)}°, ${p[0].toFixed(5)}°` : null
}

export const bboxLabel = (b) => `x ${Math.round(b[0])}–${Math.round(b[2])}, y ${Math.round(b[1])}–${Math.round(b[3])} px`
