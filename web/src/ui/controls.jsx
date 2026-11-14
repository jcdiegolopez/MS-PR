import { PauseIcon, PlayIcon, ResetIcon } from './icons.jsx'

const kmh = (v) => Math.round(v * 27)
const perKm = (rho) => Math.round((rho * 1000) / 7.5)

export function Segmented({ label, value, options, onChange, hideLabel = false }) {
  return (
    <div className="field">
      <span className={hideLabel ? 'sr-only' : 'field-label'} id={`lbl-${label}`}>
        {label}
      </span>
      <div className="segmented" role="radiogroup" aria-labelledby={`lbl-${label}`}>
        {options.map((o) => (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={value === o.value}
            className={value === o.value ? 'on' : ''}
            onClick={() => onChange(o.value)}
            title={o.title}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export function Slider({ id, label, value, min, max, step, onChange, display }) {
  return (
    <div className="field">
      <label className="field-row" htmlFor={id}>
        <span className="field-label">{label}</span>
        <output className="field-value" htmlFor={id}>
          {display}
        </output>
      </label>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ '--fill': `${((value - min) / (max - min)) * 100}%` }}
      />
    </div>
  )
}

export function Controls(props) {
  const { params, set, playing, togglePlay, reset, speed, setSpeed, view, setView } = props
  const { colorMode, setColorMode, trails, setTrails, camera, setCamera } = props
  const ring = params.scenario === 'ring'

  return (
    <div className="controls">
      <section>
        <h2>Escenario</h2>
        <Segmented
          label="Escenario"
          hideLabel
          value={params.scenario}
          onChange={(scenario) => set({ scenario })}
          options={[
            { value: 'ring', label: 'Anillo', title: 'E2: tramo periódico, sin obstáculos' },
            { value: 'bus', label: 'Bus', title: 'E3: parada de bus, toca la calle para detener uno' },
            { value: 'light', label: 'Semáforo', title: 'E4: ciclo de rojo y verde' },
          ]}
        />
        <Segmented
          label="Mostrar"
          value={view}
          onChange={setView}
          options={[
            { value: 'micro', label: 'Carros', title: 'Nivel 1: cada carro' },
            { value: 'macro', label: 'Fluido', title: 'Nivel 2: densidad (LWR)' },
            { value: 'both', label: 'Ambos', title: 'Los dos niveles superpuestos' },
          ]}
        />
      </section>

      <section>
        <h2>Conductores</h2>
        <Slider
          id="p"
          label="Distracción p"
          value={params.p}
          min={0}
          max={0.5}
          step={0.01}
          onChange={(p) => set({ p })}
          display={`${Math.round(params.p * 100)} %`}
        />
        {ring ? (
          <Slider
            id="rho"
            label="Densidad"
            value={params.rho}
            min={0.05}
            max={0.5}
            step={0.01}
            onChange={(rho) => set({ rho })}
            display={`${perKm(params.rho)} carros/km`}
          />
        ) : (
          <Slider
            id="alpha"
            label="Llegada de carros α"
            value={params.alpha}
            min={0.05}
            max={0.8}
            step={0.01}
            onChange={(alpha) => set({ alpha })}
            display={params.alpha.toFixed(2)}
          />
        )}
        <Segmented
          label="Velocidad máxima"
          value={params.vmax}
          onChange={(vmax) => set({ vmax })}
          options={[
            { value: 3, label: `${kmh(3)} km/h` },
            { value: 5, label: `${kmh(5)} km/h` },
          ]}
        />
        {params.scenario === 'light' && (
          <div className="pair">
            <Slider
              id="red"
              label="Rojo"
              value={params.red}
              min={10}
              max={90}
              step={5}
              onChange={(red) => set({ red })}
              display={`${params.red} s`}
            />
            <Slider
              id="green"
              label="Verde"
              value={params.green}
              min={10}
              max={90}
              step={5}
              onChange={(green) => set({ green })}
              display={`${params.green} s`}
            />
          </div>
        )}
      </section>

      <section>
        <h2>Simulación</h2>
        <div className="transport">
          <button type="button" className="btn primary" onClick={togglePlay} aria-label={playing ? 'Pausar' : 'Reproducir'}>
            {playing ? <PauseIcon /> : <PlayIcon />}
            <span>{playing ? 'Pausar' : 'Reproducir'}</span>
          </button>
          <button type="button" className="btn" onClick={reset} aria-label="Reiniciar con la semilla">
            <ResetIcon />
            <span>Reiniciar</span>
          </button>
          <label className="seed">
            <span>Semilla</span>
            <input
              type="number"
              min={0}
              max={9999}
              value={params.seed}
              onChange={(e) => set({ seed: Math.max(0, Math.min(9999, Math.round(Number(e.target.value) || 0))) })}
            />
          </label>
        </div>
        <Slider
          id="speed"
          label="Ritmo"
          value={speed}
          min={1}
          max={20}
          step={1}
          onChange={setSpeed}
          display={`×${speed}`}
        />
      </section>

      <section>
        <h2>Vista</h2>
        <Segmented
          label="Color de los carros"
          value={colorMode}
          onChange={setColorMode}
          options={[
            { value: 'speed', label: 'Por velocidad' },
            { value: 'stopped', label: 'Solo detenidos' },
          ]}
        />
        <Segmented
          label="Estelas"
          value={trails}
          onChange={setTrails}
          options={[
            { value: false, label: 'No' },
            { value: true, label: 'Sí' },
          ]}
        />
        <Segmented
          label="Cámara"
          value={camera}
          onChange={setCamera}
          options={[
            { value: 'near', label: 'Cerca', title: 'Unos 400 m alrededor de la acción' },
            { value: 'tilt', label: 'Toda la calle', title: 'Los 2 km en perspectiva' },
            { value: 'top', label: 'Cenital' },
            { value: 'follow', label: 'Seguir', title: 'La cámara va detrás de un carro' },
          ]}
        />
      </section>

      <p className="keys">
        <kbd>Espacio</kbd> pausa · <kbd>R</kbd> reinicia
      </p>
    </div>
  )
}
