// Maps model cells (7.5 m each) onto the real road geometry.
// Built once at startup; each frame a car's position is a lookup in this table.

const EARTH_RADIUS_M = 6371008.8
const toRad = (deg) => (deg * Math.PI) / 180
const toDeg = (rad) => (rad * 180) / Math.PI

/** Great-circle distance in meters between two [lng, lat] points. */
export function distanceM([lng1, lat1], [lng2, lat2]) {
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a =
    Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2
  return 2 * EARTH_RADIUS_M * Math.asin(Math.sqrt(a))
}

/** Compass bearing in degrees (0 = north, 90 = east) from a to b. */
export function bearingDeg([lng1, lat1], [lng2, lat2]) {
  const y = Math.sin(toRad(lng2 - lng1)) * Math.cos(toRad(lat2))
  const x =
    Math.cos(toRad(lat1)) * Math.sin(toRad(lat2)) -
    Math.sin(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.cos(toRad(lng2 - lng1))
  return (toDeg(Math.atan2(y, x)) + 360) % 360
}

/**
 * Precompute the center of every cell along a LineString.
 * Returns { lengthM, cells: [{ lng, lat, bearing }] }, with as many cells as fit in the line.
 */
export function buildCellTable(coords, cellM = 7.5) {
  const cum = [0]
  for (let i = 1; i < coords.length; i++) cum.push(cum[i - 1] + distanceM(coords[i - 1], coords[i]))
  const lengthM = cum[cum.length - 1]
  const nCells = Math.floor(lengthM / cellM)

  const cells = []
  let seg = 0
  for (let k = 0; k < nCells; k++) {
    const d = (k + 0.5) * cellM
    while (seg < coords.length - 2 && cum[seg + 1] < d) seg++
    const a = coords[seg]
    const b = coords[seg + 1]
    const f = (d - cum[seg]) / (cum[seg + 1] - cum[seg] || 1)
    cells.push({
      lng: a[0] + (b[0] - a[0]) * f,
      lat: a[1] + (b[1] - a[1]) * f,
      bearing: bearingDeg(a, b),
    })
  }
  return { lengthM, cells }
}
