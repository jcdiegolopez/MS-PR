// Turns the simulation state into deck.gl layers on the Roosevelt.
// Identity (team guide §5): the street is neon cyan, cars are the only color with
// meaning (green = vmax, red = stopped), the macro view lights the street from
// cyan (empty) to magenta and red (jam), the bus is white, the light glows.
import { PathLayer, ScatterplotLayer } from '@deck.gl/layers'
import { SimpleMeshLayer } from '@deck.gl/mesh-layers'
import { CubeGeometry } from '@luma.gl/engine'

export const CYAN = [0, 229, 255]
const MAGENTA = [255, 46, 196]
const RED = [255, 59, 48]
const YELLOW = [255, 204, 0]
const GREEN = [48, 209, 88]
const DIM = [96, 106, 122]
const WHITE = [244, 247, 250]

const CUBE = new CubeGeometry()
const CAR = [2.25, 1.0, 0.75] // half sizes in meters: 4.5 x 2 x 1.5 m
const BUS = [6.0, 1.3, 1.6] // 12 x 2.6 x 3.2 m
const MATERIAL = { ambient: 0.55, diffuse: 0.6, shininess: 24, specularColor: [60, 64, 72] }

const mix = (a, b, f) => a.map((x, i) => Math.round(x + (b[i] - x) * f))

/** Car color by speed: red (stopped) -> yellow -> green (vmax). */
export function speedColor(v, vmax) {
  const f = vmax ? v / vmax : 0
  return f < 0.5 ? mix(RED, YELLOW, f / 0.5) : mix(YELLOW, GREEN, (f - 0.5) / 0.5)
}

/**
 * Street color by density: cyan while traffic is free, turning magenta as it nears the
 * critical density rho_c (capacity), then red toward a full jam.
 */
export function densityColor(rho, rhoC) {
  if (rho <= rhoC) return mix(CYAN, MAGENTA, Math.min(1, Math.max(0, (rho / rhoC - 0.6) / 0.4)))
  return mix(MAGENTA, RED, Math.min(1, (rho - rhoC) / (0.75 - rhoC)))
}

/** Position on the street for a fractional cell index (cells are 7.5 m long). */
export function cellPoint(cells, x) {
  const n = cells.length
  const c = Math.min(Math.max(x, 0), n - 1)
  const i = Math.min(Math.floor(c), n - 2)
  const f = c - i
  const a = cells[i]
  const b = cells[i + 1]
  return { lng: a.lng + (b.lng - a.lng) * f, lat: a.lat + (b.lat - a.lat) * f, bearing: f < 0.5 ? a.bearing : b.bearing }
}

/** Nearest cell to a clicked point (equirectangular distance is enough at this scale). */
export function nearestCell(cells, [lng, lat]) {
  const k = Math.cos((lat * Math.PI) / 180)
  let best = 0
  let bestD = Infinity
  cells.forEach((c, i) => {
    const d = ((c.lng - lng) * k) ** 2 + (c.lat - lat) ** 2
    if (d < bestD) {
      bestD = d
      best = i
    }
  })
  return best
}

/** The street as one path through every cell center (the macro view colors it per vertex). */
export function buildSegments(cells) {
  return [{ path: cells.map((c) => [c.lng, c.lat]) }]
}

// Glow passes, wide and faint to thin and solid; sized to read on a projector.
const GLOW = [
  [30, 0.16],
  [15, 0.4],
  [5, 1],
]

const yaw = (bearing) => 90 - bearing // compass bearing -> rotation from east, counterclockwise

/**
 * Real cars are 4.5 m long: invisible from the overview camera. When zoomed out they are
 * drawn wider and taller (never longer than ~1.5x, so a jam of 7.5 m cells never overlaps).
 */
function boxScale(base, zoom, maxLength) {
  const k = Math.min(6, Math.max(1, 2 ** (18 - (zoom ?? 18))))
  return [base[0] * Math.min(k, maxLength), base[1] * k, base[2] * k]
}

/**
 * frame: { road, cells, segments, cars, rho, rhoC, vmax, buses, light, view, colorMode, trails, onStreetClick }
 */
export function buildLayers(frame) {
  const { road, cells, segments, cars, rho, rhoC, vmax, view, colorMode } = frame
  const showCars = view !== 'macro'
  const showMacro = view !== 'micro'
  const carScale = boxScale(CAR, frame.zoom, 1.5)
  const busScale = boxScale(BUS, frame.zoom, 1.25)
  const layers = []

  // The street: cyan glow, or lit by density in the macro views.
  if (showMacro) {
    const colors = Array.from(rho, (r) => densityColor(r, rhoC))
    GLOW.forEach(([width, a], k) => {
      // With cars on top ("Ambos"), the bright core is thinner and dimmer so the cars stand out.
      const core = k === 2 && showCars
      const alpha = Math.round(255 * (core ? 0.6 : a))
      if (core) width = 2.5
      layers.push(
        new PathLayer({
          id: `macro-${k}`,
          data: segments,
          getPath: (d) => d.path,
          getColor: () => colors.map((c) => [...c, alpha]), // one color per cell
          getWidth: width,
          widthUnits: 'pixels',
          capRounded: true,
          jointRounded: true,
          pickable: k === 0,
          updateTriggers: { getColor: [frame.t, rhoC] },
        }),
      )
    })
  } else {
    GLOW.forEach(([width, a], k) => {
      layers.push(
        new PathLayer({
          id: `road-${k}`,
          data: [{ path: road }],
          getPath: (d) => d.path,
          getColor: k === 2 ? [122, 243, 255, 255] : [...CYAN, Math.round(255 * a * 0.55)],
          getWidth: width,
          widthUnits: 'pixels',
          capRounded: true,
          jointRounded: true,
          pickable: k === 0,
        }),
      )
    })
  }

  if (showCars && frame.trails) {
    layers.push(
      new PathLayer({
        id: 'trails',
        data: frame.trailData,
        getPath: (d) => d.path,
        getColor: (d) => [...carColor(d.v, vmax, colorMode), 90],
        getWidth: 2,
        widthUnits: 'pixels',
        updateTriggers: { getColor: [frame.t, colorMode] },
      }),
    )
  }

  if (showCars) {
    layers.push(
      new SimpleMeshLayer({
        id: 'cars',
        data: cars,
        mesh: CUBE,
        material: MATERIAL,
        getPosition: (d) => [d.lng, d.lat, carScale[2]],
        getOrientation: (d) => [0, yaw(d.bearing), 0],
        getScale: carScale,
        getColor: (d) => [...carColor(d.v, vmax, colorMode), 255],
        updateTriggers: { getPosition: [frame.tick, carScale[2]], getOrientation: frame.tick, getColor: [frame.tick, colorMode, vmax] },
      }),
    )
  }

  // The moment a bus stops: a ring spreads from it for ~3 model seconds.
  const fresh = frame.buses.filter((b) => b.age < 3)
  if (fresh.length) {
    layers.push(
      new ScatterplotLayer({
        id: 'bus-drop',
        data: fresh,
        getPosition: (d) => [d.lng, d.lat, 2],
        getRadius: (d) => 8 + d.age * 22,
        radiusUnits: 'pixels',
        stroked: true,
        filled: false,
        getLineColor: (d) => [...WHITE, Math.round(220 * (1 - d.age / 3))],
        lineWidthUnits: 'pixels',
        getLineWidth: 2,
        billboard: true,
        updateTriggers: { getRadius: frame.tick, getLineColor: frame.tick },
      }),
    )
  }

  if (frame.buses.length) {
    layers.push(
      new SimpleMeshLayer({
        id: 'buses',
        data: frame.buses,
        mesh: CUBE,
        material: MATERIAL,
        getPosition: (d) => [d.lng, d.lat, busScale[2]],
        getOrientation: (d) => [0, yaw(d.bearing), 0],
        getScale: busScale,
        getColor: [...WHITE, 255],
      }),
    )
  }

  if (frame.light) {
    const { lng, lat, red, bearing } = frame.light
    const color = red ? RED : GREEN
    // Stop line across the street where the queue forms.
    const across = ((bearing + 90) * Math.PI) / 180
    const m = 9 / 111320 // ~9 m in degrees of latitude
    const dLng = (Math.sin(across) * m) / Math.cos((lat * Math.PI) / 180)
    const dLat = Math.cos(across) * m
    layers.push(
      new PathLayer({
        id: 'stop-line',
        data: [{ path: [[lng - dLng, lat - dLat], [lng + dLng, lat + dLat]] }],
        getPath: (d) => d.path,
        getColor: [...color, 255],
        getWidth: 4,
        widthUnits: 'pixels',
        capRounded: true,
        updateTriggers: { getColor: red },
      }),
    )
    layers.push(
      new ScatterplotLayer({
        id: 'light',
        data: [
          { r: 22, a: 50 },
          { r: 12, a: 120 },
          { r: 6, a: 255 },
        ],
        getPosition: [lng, lat, 7],
        getRadius: (d) => d.r,
        radiusUnits: 'pixels',
        billboard: true,
        getFillColor: (d) => [...color, d.a],
        updateTriggers: { getFillColor: red },
      }),
    )
  }

  return layers
}

function carColor(v, vmax, mode) {
  if (mode === 'stopped') return v === 0 ? RED : DIM
  return speedColor(v, vmax)
}

export { GREEN, RED, YELLOW, MAGENTA, DIM }
