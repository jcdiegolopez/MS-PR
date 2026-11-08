import { useEffect, useMemo, useState } from 'react'
import { Map, useControl } from 'react-map-gl/maplibre'
import { MapboxOverlay } from '@deck.gl/mapbox'
import { PathLayer } from '@deck.gl/layers'
import { buildCellTable } from './geo/road.js'

const BASE = import.meta.env.BASE_URL

const INITIAL_VIEW = {
  longitude: -90.5435,
  latitude: 14.6205,
  zoom: 16.3,
  pitch: 62,
  bearing: -70,
}

// Neon cyan: the only accent color of the viewer (see the team guide, §5).
const GLOW = [
  { width: 22, color: [0, 229, 255, 30] },
  { width: 12, color: [0, 229, 255, 60] },
  { width: 3, color: [122, 243, 255, 255] },
]

function DeckOverlay(props) {
  const overlay = useControl(() => new MapboxOverlay(props))
  overlay.setProps(props)
  return null
}

export default function App() {
  const [road, setRoad] = useState(null)

  useEffect(() => {
    fetch(`${BASE}roosevelt.geojson`)
      .then((r) => r.json())
      .then((geo) => setRoad(geo.features[0].geometry.coordinates))
      .catch((err) => console.error('Could not load roosevelt.geojson', err))
  }, [])

  const table = useMemo(() => (road ? buildCellTable(road) : null), [road])

  const layers = road
    ? GLOW.map(
        (g, i) =>
          new PathLayer({
            id: `road-${i}`,
            data: [{ path: road }],
            getPath: (d) => d.path,
            getColor: g.color,
            getWidth: g.width,
            widthUnits: 'pixels',
            capRounded: true,
            jointRounded: true,
          }),
      )
    : []

  return (
    <>
      <Map
        initialViewState={INITIAL_VIEW}
        mapStyle={`${BASE}dark3d.json`}
        style={{ position: 'absolute', inset: 0 }}
      >
        <DeckOverlay layers={layers} />
      </Map>
      <div className="title">
        <h1>
          <span className="dot" />
          Atascos fantasma · Calzada Roosevelt
        </h1>
        <p>{table ? `${(table.lengthM / 1000).toFixed(2)} km · ${table.cells.length} celdas de 7.5 m` : 'Cargando la calle…'}</p>
      </div>
    </>
  )
}
