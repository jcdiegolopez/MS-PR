import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Map, useControl } from 'react-map-gl/maplibre'
import { MapboxOverlay } from '@deck.gl/mapbox'
import { buildCellTable } from './geo/road.js'
import { addBus, carsAt, createSim, lightIsRed, stepSim, updateSim } from './sim/engine.js'
import { diagramForP } from './sim/godunov.js'
import { buildBand, buildLayers, buildSegments, cellPoint, nearestCell } from './view/scene.js'
import { Controls } from './ui/controls.jsx'
import { Legend, LivePanel } from './ui/live.jsx'
import { CloseIcon, SlidersIcon, TapIcon } from './ui/icons.jsx'

const BASE = import.meta.env.BASE_URL
const P_VALUES = ['0', '0.1', '0.25', '0.5']
const VMAX_VALUES = [3, 5]

// The simulated street: the first 2 km of the traced line (267 cells of 7.5 m, the same road as E3).
const ROAD_CELLS = 267
// The street heads 302° (WNW). Cameras turn the map so traffic climbs from the lower left
// toward the upper right. Nothing floats over the map any more, so framing needs no panel math.
const STREET_BEARING = 302
const MID = { longitude: -90.54248, latitude: 14.61813 }
const TILT = { ...MID, zoom: 15.6, pitch: 55, bearing: STREET_BEARING - 45 }
const PADDING = 48

/** Where the "near" camera looks: the light, the last bus, or the middle of the street. */
function focusCell(sim, n) {
  if (!sim) return Math.round(n * 0.5)
  if (sim.params.scenario === 'light') return Math.max(0, sim.lightCell - 25)
  if (sim.params.scenario === 'bus') return sim.buses.length ? Math.max(0, sim.buses[sim.buses.length - 1].cell - 20) : Math.round(n * 0.6)
  return Math.round(n * 0.5)
}

function frameStreet(map, cells, camera, sim, duration = 1200) {
  map.setPadding({ top: 0, bottom: 0, left: 0, right: 0 })
  let target
  if (camera === 'near') {
    // About 400 m of street, close enough to see each car's shape.
    const c = cellPoint(cells, focusCell(sim, cells.length))
    target = { center: [c.lng, c.lat], zoom: 17.2, pitch: 62, bearing: c.bearing - 35 }
  } else {
    const lngs = cells.map((c) => c.lng)
    const lats = cells.map((c) => c.lat)
    const bounds = [
      [Math.min(...lngs), Math.min(...lats)],
      [Math.max(...lngs), Math.max(...lats)],
    ]
    const bearing = camera === 'top' ? STREET_BEARING - 90 : STREET_BEARING - 45
    const pitch = camera === 'top' ? 0 : 55
    const cam = map.cameraForBounds(bounds, { bearing, padding: PADDING })
    if (!cam) return
    // The lat/lng box is larger than the turned street, so the street fits a little closer.
    target = { ...cam, zoom: cam.zoom + (camera === 'top' ? 0.3 : 0.45), bearing, pitch }
  }
  if (duration > 0) map.easeTo({ ...target, duration })
  else map.jumpTo(target)
}

const CAPTIONS = {
  ring: 'Tramo periódico: el carro que sale por un extremo entra por el otro. No hay ningún obstáculo; los atascos nacen solos del frenado al azar.',
  bus: 'Un bus detenido bloquea el carril: la cola crece hacia atrás y, cuando el bus sale, se disuelve.',
  light: 'La cola se forma en rojo y, en verde, se suelta como una onda que viaja hacia atrás.',
}

// The fluid model has no randomness: on the ring it starts nearly even and stays that way.
// That is one of the project's results, so the viewer says it instead of showing a flat street.
const RING_MACRO_NOTE = 'El modelo de fluido no tiene azar: sin un obstáculo, la densidad se queda pareja y no nacen atascos. Prueba Bus o Semáforo para ver la cola como una onda.'

const DEFAULTS = { scenario: 'ring', rho: 0.15, alpha: 0.3, vmax: 5, p: 0.25, seed: 3, red: 40, green: 30 }

function DeckOverlay(props) {
  const overlay = useControl(() => new MapboxOverlay(props))
  overlay.setProps(props)
  if (import.meta.env.DEV) window.__deck = overlay // for debugging in the browser console
  return null
}

export default function App() {
  const [road, setRoad] = useState(null)
  const [tables, setTables] = useState(null)
  const [error, setError] = useState(null)
  const [params, setParams] = useState(DEFAULTS)
  const [playing, setPlaying] = useState(true)
  const [speed, setSpeed] = useState(4)
  const [view, setView] = useState('micro')
  const [colorMode, setColorMode] = useState('speed')
  const [trails, setTrails] = useState(false)
  const [camera, setCamera] = useState('near')
  const [panelOpen, setPanelOpen] = useState(true)
  const [tick, setTick] = useState(0)
  const [snap, setSnap] = useState(null)
  const [zoom, setZoom] = useState(TILT.zoom)
  const [mapReady, setMapReady] = useState(false)
  const framedRef = useRef(false)

  const simRef = useRef(null)
  const accRef = useRef(0)
  const mapRef = useRef(null)
  const followRef = useRef(null)
  const playingRef = useRef(playing)
  const speedRef = useRef(speed)
  const paramsRef = useRef(params)
  const diagramRef = useRef(null)
  playingRef.current = playing
  speedRef.current = speed
  paramsRef.current = params

  // Data: the street and E1's fundamental diagrams.
  useEffect(() => {
    const get = (f) => fetch(`${BASE}${f}`).then((r) => (r.ok ? r.json() : Promise.reject(new Error(f))))
    Promise.all([
      get('roosevelt.geojson'),
      ...VMAX_VALUES.flatMap((v) => P_VALUES.map((p) => get(`fundamental_p${p}_v${v}.json`))),
    ])
      .then(([geo, ...diagrams]) => {
        setRoad(geo.features[0].geometry.coordinates)
        const t = {}
        for (const d of diagrams) (t[d.vmax] ??= {})[d.p] = d.rows.map((r) => ({ rho: r.rho, q: r.q }))
        setTables(t)
      })
      .catch((err) => setError(`No se pudieron cargar los datos (${err.message}).`))
  }, [])

  const cells = useMemo(() => (road ? buildCellTable(road).cells.slice(0, ROAD_CELLS) : null), [road])
  const street = useMemo(() => (cells ? cells.map((c) => [c.lng, c.lat]) : null), [cells])
  const segments = useMemo(() => (cells ? buildSegments(cells) : null), [cells])
  // The density band, on the street (fluid only) or beside it (with the cars).
  const band = useMemo(() => (cells ? buildBand(cells) : null), [cells])
  const bandSide = useMemo(() => (cells ? buildBand(cells, { width: 7, side: 13 }) : null), [cells])
  const diagram = useMemo(() => (tables ? diagramForP(tables[params.vmax], params.p) : null), [tables, params.vmax, params.p])
  diagramRef.current = diagram
  const qTop = useMemo(() => (tables ? diagramForP(tables[5], 0).qMax * 1.12 : 1), [tables])

  const takeSnap = useCallback(() => {
    const sim = simRef.current
    if (!sim) return
    const { red, green } = sim.params
    const phase = sim.t % (red + green)
    setSnap({
      t: sim.t,
      stats: { ...sim.stats },
      macro: { ...sim.macroStats },
      red: lightIsRed(sim),
      redLeft: phase < red ? red - phase : red + green - phase,
      buses: sim.buses.map((b) => b.tEnd - sim.t),
      inflow: sim.inflowEma,
    })
  }, [])

  // Restart when the scenario, the density or the seed changes.
  const ready = Boolean(cells && diagram)
  const reset = useCallback(() => {
    if (!cells || !diagramRef.current) return
    simRef.current = createSim(paramsRef.current, cells.length, diagramRef.current)
    accRef.current = 0
    followRef.current = null
    takeSnap()
    setTick((k) => k + 1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cells, ready, params.scenario, params.rho, params.seed, takeSnap])
  useEffect(reset, [reset])

  // Everything else changes live.
  useEffect(() => {
    if (simRef.current && diagram) updateSim(simRef.current, params, diagram)
  }, [params, diagram])

  // Animation: the model advances in 1 s steps; `speed` steps per real second; cars glide in between.
  useEffect(() => {
    let raf
    let last = performance.now()
    let lastSnap = 0
    const loop = (now) => {
      const sim = simRef.current
      const elapsed = Math.min((now - last) / 1000, 0.25)
      last = now
      if (sim && playingRef.current) {
        accRef.current += elapsed * speedRef.current
        let n = 0
        while (accRef.current >= 1 && n < 40) {
          stepSim(sim)
          accRef.current -= 1
          n++
        }
        if (n === 40) accRef.current = 0
        setTick((k) => k + 1)
        if (now - lastSnap > 250) {
          takeSnap()
          lastSnap = now
        }
      }
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [takeSnap])

  // Keyboard: Space plays or pauses, R restarts.
  useEffect(() => {
    const onKey = (e) => {
      if (e.target.closest('input, textarea, select')) return
      if (e.code === 'Space') {
        e.preventDefault()
        setPlaying((p) => !p)
      } else if (e.key === 'r' || e.key === 'R') reset()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [reset])

  // Cameras.
  useEffect(() => {
    const map = mapRef.current
    if (!map || !cells || !mapReady) return
    // The first framing is instant; later camera changes glide.
    if (camera !== 'follow') frameStreet(map, cells, camera, simRef.current, framedRef.current ? 1200 : 0)
    framedRef.current = true
    if (camera !== 'follow') followRef.current = null
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [camera, cells, mapReady, params.scenario]) // the near camera looks at each scenario's action

  // The map's box changes when the side panel opens or closes: let MapLibre redraw at the new size.
  useEffect(() => {
    const map = mapRef.current?.getMap?.()
    if (!map) return
    const id = setTimeout(() => map.resize(), 260) // after the panel's width transition
    return () => clearTimeout(id)
  }, [panelOpen, mapReady])

  const set = useCallback((changes) => setParams((p) => ({ ...p, ...changes })), [])

  const sim = simRef.current
  const f = playing ? Math.min(accRef.current, 1) : accRef.current

  const frame = useMemo(() => {
    if (!sim || !cells || !segments || !diagram) return null
    const cars = carsAt(sim, f).map((c) => ({ ...c, ...cellPoint(cells, c.x) }))
    if (camera === 'follow') {
      if (followRef.current === null || !cars.some((c) => c.id === followRef.current)) {
        const mid = cars.filter((c) => c.x > cells.length * 0.15 && c.x < cells.length * 0.7)
        followRef.current = (mid[Math.floor(mid.length / 2)] ?? cars[0])?.id ?? null
      }
      const car = cars.find((c) => c.id === followRef.current)
      if (car && mapRef.current) mapRef.current.jumpTo({ center: [car.lng, car.lat], zoom: 18.2, pitch: 68, bearing: car.bearing, padding: { top: 0, bottom: 0, left: 0, right: 0 } })
    }
    const trailData = trails
      ? sim.ids.map((id, i) => ({
          v: sim.vel[i],
          path: (sim.trails.get(id) ?? []).map((x) => {
            const pt = cellPoint(cells, x)
            return [pt.lng, pt.lat]
          }),
        }))
      : []
    const light = sim.params.scenario === 'light' ? { ...cellPoint(cells, sim.lightCell), red: lightIsRed(sim) } : null
    const buses = sim.buses.map((b) => ({ ...cellPoint(cells, b.cell), age: sim.t - b.tStart + f }))
    return { cars, trailData, light, buses }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick, f, cells, segments, diagram, camera, trails])

  const layers = useMemo(() => {
    if (!frame) return street ? buildLayers({ road: street, cells: [], segments: [], cars: [], rho: [], rhoC: 0.2, vmax: 5, view: 'micro', colorMode, buses: [] }) : []
    return buildLayers({
      road: street,
      cells,
      segments,
      rho: sim.rho,
      rhoPrev: sim.rhoPrev,
      f,
      rhoC: diagram.rhoC,
      vmax: params.vmax,
      view,
      colorMode,
      trails,
      t: sim.t,
      tick,
      zoom,
      band,
      bandSide,
      ...frame,
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [frame, view, colorMode, trails, params.vmax, street, zoom, band, bandSide])

  const onClick = useCallback(
    (info) => {
      const s = simRef.current
      if (!s || s.params.scenario !== 'bus' || !info.layer || !info.coordinate) return
      if (!/^(road|macro)-/.test(info.layer.id)) return
      addBus(s, Math.max(1, nearestCell(cells, info.coordinate)))
      takeSnap()
    },
    [cells, takeSnap],
  )

  const getCursor = useCallback(
    ({ isHovering }) => (isHovering && params.scenario === 'bus' ? 'pointer' : 'grab'),
    [params.scenario],
  )

  const ringMacro = params.scenario === 'ring' && view !== 'micro'

  return (
    <div className={`app ${panelOpen ? 'panel-open' : 'panel-closed'}`}>
      <aside className="sidebar" aria-label="Simulación: datos en vivo y controles">
        <div className="sidebar-head">
          {panelOpen && (
            <div className="title">
              <h1>
                <span className="dot" />
                Atascos fantasma · Calzada Roosevelt
              </h1>
              <p>{error ?? CAPTIONS[params.scenario]}</p>
            </div>
          )}
          <button
            type="button"
            className="panel-toggle"
            onClick={() => setPanelOpen((o) => !o)}
            aria-expanded={panelOpen}
            aria-label={panelOpen ? 'Ocultar el panel' : 'Mostrar el panel'}
            title={panelOpen ? 'Ocultar el panel' : 'Mostrar el panel'}
          >
            {panelOpen ? <CloseIcon /> : <SlidersIcon />}
          </button>
        </div>

        {panelOpen && (
          <div className="sidebar-body">
            {ringMacro && <p className="note">{RING_MACRO_NOTE}</p>}
            <LivePanel snap={snap} diagram={diagram} qTop={qTop} view={view} scenario={params.scenario} />
            <Legend view={view} colorMode={colorMode} vmax={params.vmax} />
            <Controls
              params={params}
              set={set}
              playing={playing}
              togglePlay={() => setPlaying((p) => !p)}
              reset={reset}
              speed={speed}
              setSpeed={setSpeed}
              view={view}
              setView={setView}
              colorMode={colorMode}
              setColorMode={setColorMode}
              trails={trails}
              setTrails={setTrails}
              camera={camera}
              setCamera={setCamera}
            />
          </div>
        )}
      </aside>

      <main className="stage">
        <Map
          ref={mapRef}
          initialViewState={TILT}
          onLoad={(e) => {
            if (import.meta.env.DEV) window.__map = e.target // for debugging in the browser console
            setMapReady(true)
          }}
          mapStyle={`${BASE}dark3d.json`}
          style={{ position: 'absolute', inset: 0 }}
          attributionControl={{ compact: false }}
          onMove={(e) => setZoom(Math.round(e.viewState.zoom * 10) / 10)}
          onDragStart={() => camera === 'follow' && setCamera('tilt')}
        >
          <DeckOverlay layers={layers} onClick={onClick} getCursor={getCursor} pickingRadius={14} />
        </Map>

        {params.scenario === 'bus' && !error && (
          <div className="hint" role="note">
            <TapIcon />
            {snap?.buses.length ? 'Toca otra vez para otro bus' : 'Toca la calle para detener un bus 30 s'}
          </div>
        )}
      </main>
    </div>
  )
}
