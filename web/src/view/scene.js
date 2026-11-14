// Turns the simulation state into deck.gl layers on the Roosevelt.
// Identity: the street has a neon cyan edge, cars are colored by speed (green = vmax,
// red = stopped), and the macro view is a 3D band beside or on the street that rises
// with density and uses map-app traffic colors (green flows, dark red is a jam).
import { PathLayer, ScatterplotLayer, SolidPolygonLayer } from '@deck.gl/layers'
import { ScenegraphLayer, SimpleMeshLayer } from '@deck.gl/mesh-layers'
import { CubeGeometry } from '@luma.gl/engine'

export const CYAN = [0, 229, 255]
const MAGENTA = [255, 46, 196]
const RED = [255, 59, 48]
const YELLOW = [255, 204, 0]
const GREEN = [48, 209, 88]
const DIM = [96, 106, 122]
const WHITE = [244, 247, 250]

const CUBE = new CubeGeometry()

// Low-poly models made in Blender for this project (assets/visor-modelos.blend). Z up, front
// toward +X, origin on the ground. The car body is white so getColor can tint it by speed.
const MODELS = `${import.meta.env.BASE_URL}models/`
const CAR_MODEL = `${MODELS}carro.glb`
const BUS_MODEL = `${MODELS}bus.glb`
const LIGHT_MODEL = `${MODELS}semaforo.glb`
// From this zoom on, cars are drawn as models; farther out they are enlarged colored blocks.
const MODEL_ZOOM = 16
// In the model the arm reaches 5.6 m toward -Y, which is the right of the direction of travel,
// so the pole stands 6 m to the LEFT of the lane and the lamps hang over it.
const LIGHT_POLE_SIDE_M = 6
const LIGHT_ARM_M = 5.6
const LIGHT_HEAD_M = 5.1 // height of the middle lamp
const CAR = [2.25, 1.0, 0.75] // half sizes in meters: 4.5 x 2 x 1.5 m
const BUS = [6.0, 1.3, 1.6] // 12 x 2.6 x 3.2 m
const MATERIAL = { ambient: 0.55, diffuse: 0.6, shininess: 24, specularColor: [60, 64, 72] }

const mix = (a, b, f) => a.map((x, i) => Math.round(x + (b[i] - x) * f))

/** Car color by speed: red (stopped) -> yellow -> green (vmax). */
export function speedColor(v, vmax) {
  const f = vmax ? v / vmax : 0
  return f < 0.5 ? mix(RED, YELLOW, f / 0.5) : mix(YELLOW, GREEN, (f - 0.5) / 0.5)
}

const JAM = [140, 20, 40] // dark red: cars standing still, bumper to bumper

/**
 * Density color in map-app traffic colors, measured against the critical density rho_c
 * (the road's capacity): green well below it, yellow at it, red past it, dark red near a full jam.
 */
export function densityColor(rho, rhoC) {
  const f = rhoC > 0 ? rho / rhoC : 0
  if (f <= 0.6) return GREEN
  if (f <= 1) return mix(GREEN, YELLOW, (f - 0.6) / 0.4)
  if (f <= 2) return mix(YELLOW, RED, f - 1)
  return mix(RED, JAM, Math.min(1, (f - 2) / 2))
}

// Meters -> degrees near the Roosevelt (latitude ~14.6°).
const M_LAT = 1 / 111320
const mLng = (lat) => 1 / (111320 * Math.cos((lat * Math.PI) / 180))

/** Shift a point `east`/`north` meters. */
const offset = (lng, lat, east, north) => [lng + east * mLng(lat), lat + north * M_LAT]

/**
 * The density band: one quad per cell, 7.5 m long and `width` m wide, moved `side` m to the
 * right of the direction of travel (0 = on the street). Built once; heights and colors change.
 */
export function buildBand(cells, { width = 9, side = 0 } = {}) {
  return cells.map((c, i) => {
    const b = (c.bearing * Math.PI) / 180
    const along = [Math.sin(b), Math.cos(b)] // unit vector (east, north) along the street
    const right = [Math.cos(b), -Math.sin(b)] // unit vector to the right of travel
    const corner = (a, s) => offset(c.lng, c.lat, along[0] * a + right[0] * s, along[1] * a + right[1] * s)
    const h = 3.75
    const w0 = side - width / 2
    const w1 = side + width / 2
    return { i, polygon: [corner(-h, w0), corner(h, w0), corner(h, w1), corner(-h, w1)] }
  })
}

// Height of the band for a full jam (1 car per 7.5 m cell); a free street stays almost flat.
// Tall enough to read across 2 km, lower up close so it does not hide the cars.
function bandHeight(zoom = 15) {
  const f = Math.min(1, Math.max(0, (zoom - 15) / 3)) // 0 at zoom 15, 1 at zoom 18
  return 60 - f * 50 // 60 m far away -> 10 m up close
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

// The street, drawn in meters so it widens as you zoom in: a faint cyan glow, a cyan edge
// and a dark asphalt lane on top. The minimum pixel widths keep it visible from far away.
const STREET = [
  { id: 'glow', width: 30, minPx: 26, color: [...CYAN, 40] },
  { id: 'edge', width: 13, minPx: 7, color: [...CYAN, 210] },
  { id: 'lane', width: 10, minPx: 3, color: [24, 28, 36, 255] },
]

const yaw = (bearing) => 90 - bearing // compass bearing -> rotation from east, counterclockwise

/**
 * Models are drawn wider and taller than life so they read on a projector, more so as the
 * camera pulls back. Length stays below a 7.5 m cell so the cars of a jam never overlap.
 * Model axes: x = length (front), y = width, z = height.
 */
function modelGrow(zoom = 18) {
  return Math.min(1.6, Math.max(1, 2 ** ((18 - zoom) / 2))) // 1 at zoom 18, 1.6 from ~16.6
}
const carModelScale = (zoom) => {
  const k = modelGrow(zoom)
  return [Math.min(1.55, 1.3 * k), 1.7 * k, 1.6 * k] // at most 6.9 m long
}
const busModelScale = (zoom) => {
  const k = modelGrow(zoom)
  return [1.15, 1.5 * k, 1.4 * k]
}
// The traffic light is a single landmark: exaggerated on purpose so it is found at a glance.
const lightScale = (close) => (close ? 2.5 : 4)

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

  // The street, always: it is what you click to stop a bus.
  STREET.forEach((s, k) => {
    layers.push(
      new PathLayer({
        id: `road-${s.id}`,
        data: [{ path: road }],
        getPath: (d) => d.path,
        getColor: s.color,
        getWidth: s.width,
        widthUnits: 'meters',
        widthMinPixels: s.minPx,
        capRounded: true,
        jointRounded: true,
        pickable: k === 0,
      }),
    )
  })

  // The fluid (level 2): a band that rises with density. On its own it sits on the street;
  // with the cars ("Ambos") it moves beside the street so both levels are visible.
  if (showMacro && frame.band) {
    // The PDE advances in 1 s steps; blend the last two states so the band rises smoothly.
    const prev = frame.rhoPrev ?? rho
    const f = Math.min(1, Math.max(0, frame.f ?? 1))
    const rhoAt = (i) => prev[i] + (rho[i] - prev[i]) * f
    layers.push(
      new SolidPolygonLayer({
        id: 'macro-band',
        data: showCars ? frame.bandSide : frame.band,
        getPolygon: (d) => d.polygon,
        extruded: true,
        getElevation: (d) => 0.5 + rhoAt(d.i) * bandHeight(frame.zoom),
        getFillColor: (d) => [...densityColor(rhoAt(d.i), rhoC), 235],
        material: { ambient: 0.6, diffuse: 0.5, shininess: 8 },
        pickable: true,
        updateTriggers: { getElevation: [frame.tick, frame.zoom], getFillColor: [frame.tick, rhoC] },
      }),
    )
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

  const close = (frame.zoom ?? 0) >= MODEL_ZOOM

  if (showCars && close) {
    layers.push(
      new ScenegraphLayer({
        id: 'cars-model',
        data: cars,
        scenegraph: CAR_MODEL,
        _lighting: 'pbr',
        getPosition: (d) => [d.lng, d.lat, 0],
        getOrientation: (d) => [0, yaw(d.bearing), 0],
        getScale: carModelScale(frame.zoom),
        getColor: (d) => [...carColor(d.v, vmax, colorMode), 255],
        updateTriggers: { getPosition: frame.tick, getOrientation: frame.tick, getColor: [frame.tick, colorMode, vmax] },
      }),
    )
  } else if (showCars) {
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
      close
        ? new ScenegraphLayer({
            id: 'buses-model',
            data: frame.buses,
            scenegraph: BUS_MODEL,
            _lighting: 'pbr',
            getPosition: (d) => [d.lng, d.lat, 0],
            getOrientation: (d) => [0, yaw(d.bearing), 0],
            getScale: busModelScale(frame.zoom),
          })
        : new SimpleMeshLayer({
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
    // The pole stands to the left of travel; scaled with the model so the head stays over the lane.
    const s = lightScale(close)
    const b = (bearing * Math.PI) / 180
    const left = [-Math.cos(b), Math.sin(b)] // unit vector (east, north) to the left of travel
    const pole = offset(lng, lat, left[0] * LIGHT_POLE_SIDE_M * s, left[1] * LIGHT_POLE_SIDE_M * s)
    const headSide = (LIGHT_POLE_SIDE_M - LIGHT_ARM_M) * s
    const head = offset(lng, lat, left[0] * headSide, left[1] * headSide)
    layers.push(
      new ScenegraphLayer({
        id: 'light-model',
        data: [{ position: [...pole, 0] }],
        scenegraph: LIGHT_MODEL,
        _lighting: 'pbr',
        sizeScale: s,
        getPosition: (d) => d.position,
        getOrientation: [0, yaw(bearing), 0],
        updateTriggers: { getPosition: s },
      }),
    )
    layers.push(
      new ScatterplotLayer({
        id: 'light',
        data: close
          ? [
              { r: 16, a: 60 },
              { r: 8, a: 140 },
              { r: 4, a: 255 },
            ]
          : [
              { r: 22, a: 50 },
              { r: 12, a: 120 },
              { r: 6, a: 255 },
            ],
        getPosition: [...head, LIGHT_HEAD_M * s],
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
