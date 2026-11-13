// Level 1 in JavaScript: a port of src/micro.py (Nagel-Schreckenberg).
// Same conventions as Python: model units (cells, steps), `pos` sorted ascending
// (index 0 is the rearmost car), all cars updated in parallel from the old state.
// The official results come from Python; tests/nasch.test.js checks this port
// against a trajectory exported from it.

/** Seeded generator in [0, 1). It does not match numpy's numbers, only its role. */
export function mulberry32(seed) {
  let a = seed >>> 0
  return function rand() {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** round(rho * L) cars at distinct random cells, speed 0 (like init_ring). */
export function initRing(L, rho, rand) {
  const n = Math.round(rho * L)
  const cells = Int32Array.from({ length: L }, (_, i) => i)
  for (let i = 0; i < n; i++) {
    const j = i + Math.floor(rand() * (L - i))
    const tmp = cells[i]
    cells[i] = cells[j]
    cells[j] = tmp
  }
  const pos = cells.slice(0, n).sort()
  return { pos, vel: new Int32Array(n) }
}

function sortByPos(pos, vel) {
  const order = Array.from(pos.keys()).sort((a, b) => pos[a] - pos[b])
  return {
    pos: Int32Array.from(order, (i) => pos[i]),
    vel: Int32Array.from(order, (i) => vel[i]),
  }
}

/** One parallel update of the 4 rules on a ring road (step_ring). */
export function stepRing(pos, vel, L, vmax, p, rand) {
  const n = pos.length
  if (n === 0) return { pos: pos.slice(), vel: vel.slice() }
  const newPos = new Int32Array(n)
  const newVel = new Int32Array(n)
  for (let i = 0; i < n; i++) {
    const ahead = pos[(i + 1) % n]
    const gap = (((ahead - pos[i] - 1) % L) + L) % L
    let v = Math.min(vel[i] + 1, vmax) // 1. accelerate
    v = Math.min(v, gap) // 2. brake to the gap
    if (rand() < p) v = Math.max(v - 1, 0) // 3. random braking
    newVel[i] = v
    newPos[i] = (pos[i] + v) % L // 4. move
  }
  return sortByPos(newPos, newVel)
}

/**
 * One step of the open road (one iteration of run_open's loop).
 * `obstacles` are { cell, tStart, tEnd } blocking `cell` while tStart <= t < tEnd.
 * Returns the new state plus `inserted` (0 or 1) and `exited` (cars that left the road).
 */
export function stepOpen(pos, vel, L, vmax, p, alpha, obstacles, t, rand) {
  let n = pos.length
  let outPos = pos
  let outVel = vel
  let exited = 0

  if (n > 0) {
    const active = obstacles.filter((o) => o.tStart <= t && t < o.tEnd).map((o) => o.cell)
    const newPos = []
    const newVel = []
    for (let i = 0; i < n; i++) {
      // The leader sees vmax empty cells past the end, so it leaves freely.
      const next = i + 1 < n ? pos[i + 1] : L + vmax
      let gap = next - pos[i] - 1
      for (const cell of active) if (pos[i] < cell) gap = Math.min(gap, cell - pos[i] - 1)
      let v = Math.min(vel[i] + 1, vmax)
      v = Math.min(v, gap)
      if (rand() < p) v = Math.max(v - 1, 0)
      const x = pos[i] + v
      if (x < L) {
        newPos.push(x)
        newVel.push(v)
      } else exited++
    }
    outPos = Int32Array.from(newPos)
    outVel = Int32Array.from(newVel)
    n = outPos.length
  }

  // Entry after movement, at most once per step; the new car is not faster than its gap.
  let inserted = 0
  if ((n === 0 || outPos[0] > 0) && rand() < alpha) {
    const gap = n ? outPos[0] - 1 : vmax
    const p2 = new Int32Array(n + 1)
    const v2 = new Int32Array(n + 1)
    p2.set(outPos, 1)
    v2.set(outVel, 1)
    v2[0] = Math.min(vmax, gap)
    outPos = p2
    outVel = v2
    inserted = 1
  }
  return { pos: outPos, vel: outVel, inserted, exited }
}

/** Instant measures in model units: flow (cars/step), mean speed (cells/step), fraction stopped. */
export function measure(pos, vel, L) {
  const n = vel.length
  let sum = 0
  let stopped = 0
  for (let i = 0; i < n; i++) {
    sum += vel[i]
    if (vel[i] === 0) stopped++
  }
  return {
    density: n / L,
    flow: sum / L,
    meanSpeed: n ? sum / n : 0,
    fracStopped: n ? stopped / n : 0,
  }
}
