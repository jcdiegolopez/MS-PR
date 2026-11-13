// Level 2 in JavaScript: a port of src/macro.py and src/fundamental.py
// (LWR solved with the Godunov / cell transmission scheme).
// Model units: dx in cells, dt in steps, rho in cars/cell, q in cars/step.
// n cells have n + 1 interfaces: F[i] enters cell i, F[i + 1] leaves it.

/** One finite-volume step (godunov_step). `cap` limits each interface (0 = blocked). */
export function godunovStep(rho, Q, rhoC, dt, dx, inflow, outSupply, cap = null) {
  const n = rho.length
  const D = new Float64Array(n)
  const S = new Float64Array(n)
  for (let i = 0; i < n; i++) {
    D[i] = Q(Math.min(rho[i], rhoC)) // what the cell can send
    S[i] = Q(Math.max(rho[i], rhoC)) // what the cell can receive
  }
  const F = new Float64Array(n + 1)
  F[0] = Math.min(inflow, S[0])
  for (let i = 1; i < n; i++) F[i] = Math.min(D[i - 1], S[i])
  F[n] = Math.min(D[n - 1], outSupply)
  if (cap) for (let i = 0; i <= n; i++) F[i] = Math.min(F[i], cap[i])
  const out = new Float64Array(n)
  for (let i = 0; i < n; i++) out[i] = rho[i] - (dt / dx) * (F[i + 1] - F[i])
  return out
}

/** Same scheme on a ring: what leaves the last cell enters the first. */
export function godunovStepRing(rho, Q, rhoC, dt, dx) {
  const n = rho.length
  const D = new Float64Array(n)
  const S = new Float64Array(n)
  for (let i = 0; i < n; i++) {
    D[i] = Q(Math.min(rho[i], rhoC))
    S[i] = Q(Math.max(rho[i], rhoC))
  }
  const out = new Float64Array(n)
  for (let i = 0; i < n; i++) {
    const fin = Math.min(D[(i - 1 + n) % n], S[i])
    const fout = Math.min(D[i], S[(i + 1) % n])
    out[i] = rho[i] - (dt / dx) * (fout - fin)
  }
  return out
}

/** Largest stable time step (cfl_dt). */
export function cflDt(dx, vmax, safety = 0.9) {
  return (safety * dx) / vmax
}

/** Parabolic diagram (greenshields). */
export function greenshields(vf, rhoJ = 1) {
  return { Q: (r) => vf * r * (1 - r / rhoJ), rhoC: rhoJ / 2, qMax: (vf * rhoJ) / 4 }
}

/** Linear interpolation of a measured table, with Q(0) = Q(1) = 0 (load_measured). */
export function measuredDiagram(rows) {
  const inner = rows.filter((r) => r.rho > 0 && r.rho < 1).sort((a, b) => a.rho - b.rho)
  const xs = [0, ...inner.map((r) => r.rho), 1]
  const ys = [0, ...inner.map((r) => r.q), 0]
  let k = 0
  for (let i = 1; i < ys.length; i++) if (ys[i] > ys[k]) k = i
  const Q = (r) => {
    if (r <= xs[0]) return ys[0]
    if (r >= xs[xs.length - 1]) return ys[ys.length - 1]
    let lo = 0
    let hi = xs.length - 1
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1
      if (xs[mid] <= r) lo = mid
      else hi = mid
    }
    const f = (r - xs[lo]) / (xs[hi] - xs[lo])
    return ys[lo] + f * (ys[hi] - ys[lo])
  }
  return { Q, rhoC: xs[k], qMax: ys[k], xs, ys }
}

/**
 * Diagram for any p between the measured ones (E1 has p = 0, 0.1, 0.25, 0.5):
 * flow interpolated linearly in p on a shared density grid.
 * `tables` maps p -> rows [{ rho, q }].
 */
export function diagramForP(tables, p) {
  const ps = Object.keys(tables).map(Number).sort((a, b) => a - b)
  const pc = Math.min(Math.max(p, ps[0]), ps[ps.length - 1])
  let i = 0
  while (i < ps.length - 2 && ps[i + 1] < pc) i++
  const [p0, p1] = [ps[i], ps[i + 1] ?? ps[i]]
  const w = p1 === p0 ? 0 : (pc - p0) / (p1 - p0)
  const a = measuredDiagram(tables[p0])
  const b = measuredDiagram(tables[p1])
  const rows = a.xs.slice(1, -1).map((rho) => ({ rho, q: (1 - w) * a.Q(rho) + w * b.Q(rho) }))
  return { ...measuredDiagram(rows), exact: w === 0 || w === 1, p: pc }
}
