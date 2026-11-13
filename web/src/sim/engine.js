// Runs both levels side by side for the viewer, one model step (1 s) at a time.
// The physics lives in nasch.js and godunov.js; this file only keeps the scenario
// state, car identities (for smooth drawing) and running measures.
import { cflDt, godunovStep, godunovStepRing } from './godunov.js'
import { initRing, measure, mulberry32, stepOpen, stepRing } from './nasch.js'

export const BUS_SECONDS = 30
const TRAIL = 20 // steps kept per car for trails
const EMA = 1 / 30 // smoothing of the live counters (~30 s memory)
const INFLOW_EMA = 1 / 60

/**
 * params: { scenario: 'ring' | 'bus' | 'light', rho, alpha, vmax, p, seed, red, green }
 * diagram: { Q, rhoC, qMax } for the current p and vmax (from E1).
 */
export function createSim(params, L, diagram) {
  const rand = mulberry32(params.seed)
  const sim = {
    params: { ...params },
    L,
    t: 0,
    rand,
    pos: new Int32Array(0),
    vel: new Int32Array(0),
    ids: [],
    nextId: 0,
    prev: new Map(), // id -> cell at the previous step (for interpolation)
    trails: new Map(), // id -> recent cells
    buses: [], // { cell, tStart, tEnd }
    lightCell: Math.round(L * 0.62),
    diagram,
    rho: new Float64Array(L),
    inflowEma: 0,
    stats: null,
    macroStats: null,
  }

  if (params.scenario === 'ring') {
    const { pos, vel } = initRing(L, params.rho, rand)
    sim.pos = pos
    sim.vel = vel
    sim.ids = Array.from(pos, () => sim.nextId++)
    sim.rho = smoothOccupancy(pos, L)
  }
  sim.ids.forEach((id, i) => sim.prev.set(id, sim.pos[i]))
  sim.stats = measure(sim.pos, sim.vel, L)
  sim.macroStats = macroMeasure(sim)

  // Open roads start empty: fill them before showing anything.
  if (params.scenario !== 'ring') for (let k = 0; k < Math.ceil((3 * L) / params.vmax); k++) stepSim(sim)
  return sim
}

/** Live parameter changes that do not need a restart. */
export function updateSim(sim, changes, diagram) {
  Object.assign(sim.params, changes)
  if (diagram) sim.diagram = diagram
}

export function addBus(sim, cell) {
  sim.buses.push({ cell, tStart: sim.t, tEnd: sim.t + BUS_SECONDS })
}

export function lightIsRed(sim, t = sim.t) {
  const { red, green } = sim.params
  return t % (red + green) < red
}

function activeObstacles(sim) {
  const out = sim.buses.filter((b) => b.tStart <= sim.t && sim.t < b.tEnd)
  if (sim.params.scenario === 'light' && lightIsRed(sim)) out.push({ cell: sim.lightCell, tStart: sim.t, tEnd: sim.t + 1 })
  return out
}

/** Advance both levels by one model step. */
export function stepSim(sim) {
  const { scenario, vmax, p, alpha } = sim.params
  const L = sim.L
  const obstacles = activeObstacles(sim)

  sim.prev = new Map(sim.ids.map((id, i) => [id, sim.pos[i]]))

  // Level 1
  if (scenario === 'ring') {
    const sumBefore = sim.pos.reduce((a, b) => a + b, 0)
    const next = stepRing(sim.pos, sim.vel.map((v) => Math.min(v, vmax)), L, vmax, p, sim.rand)
    // Cars never overtake, so the order only rotates: the k cars that wrapped move to the front.
    const sumAfter = next.pos.reduce((a, b) => a + b, 0)
    const sumVel = next.vel.reduce((a, b) => a + b, 0)
    const k = Math.round((sumBefore + sumVel - sumAfter) / L)
    sim.ids = k ? [...sim.ids.slice(-k), ...sim.ids.slice(0, -k)] : sim.ids
    sim.pos = next.pos
    sim.vel = next.vel
  } else {
    const next = stepOpen(sim.pos, sim.vel.map((v) => Math.min(v, vmax)), L, vmax, p, alpha, obstacles, sim.t, sim.rand)
    let ids = next.exited ? sim.ids.slice(0, sim.ids.length - next.exited) : sim.ids
    if (next.inserted) ids = [sim.nextId++, ...ids]
    sim.ids = ids
    sim.pos = next.pos
    sim.vel = next.vel
    sim.inflowEma += INFLOW_EMA * (next.inserted - sim.inflowEma)
  }

  // Level 2: as many sub-steps as the CFL condition needs to cover 1 s.
  const { Q, rhoC, qMax } = sim.diagram
  const sub = Math.ceil(1 / cflDt(1, vmax))
  const dt = 1 / sub
  let cap = null
  if (scenario !== 'ring' && obstacles.length) {
    cap = new Float64Array(L + 1).fill(Infinity)
    for (const o of obstacles) cap[o.cell] = 0 // interface in front of the blocked cell
  }
  for (let s = 0; s < sub; s++) {
    sim.rho =
      scenario === 'ring'
        ? godunovStepRing(sim.rho, Q, rhoC, dt, 1)
        : godunovStep(sim.rho, Q, rhoC, dt, 1, sim.inflowEma, qMax, cap)
  }

  sim.t += 1
  sim.buses = sim.buses.filter((b) => b.tEnd > sim.t)
  updateTrails(sim)
  ema(sim, 'stats', measure(sim.pos, sim.vel, L))
  ema(sim, 'macroStats', macroMeasure(sim))
}

// A plain running mean for the first 30 s, then an exponential one.
function ema(sim, key, now) {
  const old = sim[key]
  if (!old) return void (sim[key] = now)
  const w = Math.max(EMA, 1 / (sim.t + 1))
  for (const k of Object.keys(now)) old[k] += w * (now[k] - old[k])
}

function macroMeasure(sim) {
  const { Q, rhoC } = sim.diagram
  let mass = 0
  let flux = 0
  for (const r of sim.rho) {
    mass += r
    flux += Math.min(Q(Math.min(r, rhoC)), Q(Math.max(r, rhoC))) // the cell's own flow Q(rho)
  }
  return { density: mass / sim.L, flow: flux / sim.L }
}

function updateTrails(sim) {
  const alive = new Map()
  sim.ids.forEach((id, i) => {
    const trail = sim.trails.get(id) ?? []
    const x = sim.pos[i]
    if (trail.length && x < trail[trail.length - 1]) trail.length = 0 // wrapped around: start over
    trail.push(x)
    if (trail.length > TRAIL) trail.shift()
    alive.set(id, trail)
  })
  sim.trails = alive
}

/** Occupancy averaged over 10-cell windows (the same density the report uses for level 1). */
export function smoothOccupancy(pos, L, w = 10) {
  const occ = new Float64Array(L)
  for (const x of pos) occ[x] = 1
  const out = new Float64Array(L)
  for (let i = 0; i < L; i++) {
    let s = 0
    for (let k = -Math.floor(w / 2); k < Math.ceil(w / 2); k++) s += occ[(i + k + L) % L]
    out[i] = s / w
  }
  return out
}

/** Where each car should be drawn, f in [0, 1] of the way from the last step to the current one. */
export function carsAt(sim, f) {
  const out = []
  sim.ids.forEach((id, i) => {
    const now = sim.pos[i]
    const before = sim.prev.get(id)
    let x = now
    if (before !== undefined) {
      const moved = (now - before + sim.L) % sim.L // handles the wrap on the ring
      x = (before + f * moved) % sim.L
    }
    out.push({ id, x, v: sim.vel[i] })
  })
  return out
}
