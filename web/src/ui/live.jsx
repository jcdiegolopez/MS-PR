// Live panel: counters in real units and the fundamental diagram from E1 with the current state on it.
const nf = new Intl.NumberFormat('es-GT', { maximumFractionDigits: 0 })
// Drawn in a wide panel now, so the chart gets real room and axis titles.
const W = 360
const H = 220
const PAD = { l: 40, r: 10, t: 10, b: 34 }
const KM = 1000 / 7.5 // cars/cell -> cars/km
const HOUR = 3600 // cars/step -> cars/h

function Readout({ label, value, unit, tone }) {
  return (
    <div className={`readout ${tone ?? ''}`}>
      <span className="readout-label">{label}</span>
      <span className="readout-value">
        {value}
        <small>{unit}</small>
      </span>
    </div>
  )
}

export function LivePanel({ snap, diagram, qTop, view, scenario }) {
  if (!snap || !diagram) return null
  const { stats, macro, t, red, redLeft, buses, inflow } = snap
  const showMicro = view !== 'macro'
  const showMacro = view !== 'micro'
  const src = showMicro ? stats : macro

  const x = (rho) => PAD.l + (rho * KM * (W - PAD.l - PAD.r)) / KM
  const y = (q) => H - PAD.b - (q / qTop) * (H - PAD.t - PAD.b)
  const curve = diagram.xs.map((r, i) => `${i ? 'L' : 'M'}${x(r).toFixed(1)},${y(diagram.ys[i]).toFixed(1)}`).join('')
  const ticksY = [0, 1000, 2000, 3000].filter((v) => v / HOUR <= qTop)
  const mm = String(Math.floor(t / 60)).padStart(2, '0')
  const ss = String(t % 60).padStart(2, '0')

  return (
    <div className="live" aria-live="off">
      <div className="live-head">
        <span>Simulado · {showMicro ? 'nivel 1, carros' : 'nivel 2, fluido'}</span>
        <span className="clock">
          t = {mm}:{ss}
        </span>
      </div>

      <div className="readouts">
        <Readout label="Flujo" value={nf.format(src.flow * HOUR)} unit="carros/h" />
        <Readout label="Densidad" value={nf.format(src.density * KM)} unit="carros/km" />
        {showMicro ? (
          <>
            <Readout label="Velocidad media" value={nf.format(stats.meanSpeed * 27)} unit="km/h" />
            <Readout label="Detenidos" value={nf.format(stats.fracStopped * 100)} unit="%" tone={stats.fracStopped > 0.05 ? 'hot' : ''} />
          </>
        ) : (
          <>
            <Readout label="Capacidad" value={nf.format(diagram.qMax * HOUR)} unit="carros/h" />
            <Readout label="Densidad crítica" value={nf.format(diagram.rhoC * KM)} unit="carros/km" />
          </>
        )}
      </div>

      {scenario === 'light' && (
        <p className={`status ${red ? 'red' : 'green'}`}>
          <span className="lamp" /> {red ? 'Rojo' : 'Verde'} · cambia en {redLeft} s
        </p>
      )}
      {scenario === 'bus' && (
        <p className="status">
          {buses.length ? `${buses.length === 1 ? 'Bus detenido' : `${buses.length} buses detenidos`} · sale en ${buses[0]} s` : 'Sin buses'}
          {' · '}
          llegan {nf.format(inflow * HOUR)} carros/h
        </p>
      )}

      <figure className="fd">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Diagrama fundamental: flujo contra densidad, con el estado actual">
          {ticksY.map((v) => (
            <g key={v}>
              <line x1={PAD.l} x2={W - PAD.r} y1={y(v / HOUR)} y2={y(v / HOUR)} className="grid" />
              <text x={PAD.l - 5} y={y(v / HOUR) + 3} className="tick" textAnchor="end">
                {v / 1000}k
              </text>
            </g>
          ))}
          {[0, 20, 40, 60, 80, 100, 120].map((d) => (
            <text key={d} x={x(d / KM)} y={H - PAD.b + 14} className="tick" textAnchor="middle">
              {d}
            </text>
          ))}
          <text x={(PAD.l + W - PAD.r) / 2} y={H - 3} className="axis" textAnchor="middle">
            densidad (carros/km)
          </text>
          <text x={11} y={(PAD.t + H - PAD.b) / 2} className="axis" textAnchor="middle" transform={`rotate(-90 11 ${(PAD.t + H - PAD.b) / 2})`}>
            flujo (carros/h)
          </text>
          <text x={x(diagram.rhoC) + 4} y={PAD.t + 10} className="tick">
            capacidad
          </text>
          <line x1={x(diagram.rhoC)} x2={x(diagram.rhoC)} y1={PAD.t} y2={H - PAD.b} className="crit" />
          <path d={curve} className="curve" />
          {showMacro && <circle cx={x(macro.density)} cy={y(macro.flow)} r="5.5" className="dot-macro" />}
          {showMicro && <circle cx={x(stats.density)} cy={y(stats.flow)} r="4.5" className="dot-micro" />}
        </svg>
        <figcaption>
          <span>Diagrama fundamental de E1{diagram.exact ? '' : ' (interpolado en p)'}: flujo contra densidad</span>
          {showMicro && showMacro && (
            <span className="fd-key">
              <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
                <circle cx="6" cy="6" r="4" className="dot-micro" />
              </svg>
              carros
              <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
                <circle cx="6" cy="6" r="4" className="dot-macro" />
              </svg>
              fluido
            </span>
          )}
        </figcaption>
      </figure>
    </div>
  )
}

export function Legend({ view, colorMode, vmax }) {
  return (
    <div className="legend" aria-label="Leyenda de colores">
      {view !== 'macro' &&
        (colorMode === 'speed' ? (
          <div className="legend-row">
            <span>detenido</span>
            <span className="ramp speed grow" />
            <span>{vmax * 27} km/h</span>
          </div>
        ) : (
          <div className="legend-row">
            <span className="swatch stop" /> <span>carro detenido</span>
          </div>
        ))}
      {view !== 'micro' && (
        <>
          <div className="legend-row">
            <span>fluye</span>
            <span className="ramp density grow" />
            <span>atasco</span>
          </div>
          <p className="legend-note">En el fluido, la franja sube donde hay más carros por km: una cola se ve como una montaña.</p>
        </>
      )}
    </div>
  )
}
