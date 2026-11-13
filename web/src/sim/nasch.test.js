// Equivalence test: the JavaScript port must say the same as the official Python model.
// Fixtures come from `python -m experiments.export_fixtures` (repo root).
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { initRing, measure, mulberry32, stepOpen, stepRing } from './nasch.js'
import ring from './__fixtures__/nasch_p0.json'
import open from './__fixtures__/nasch_open_p0.json'

const neverBrake = () => 0.99 // with p = 0 the draw never matters

function spacetimeRow(pos, vel, L) {
  const row = new Array(L).fill(-1)
  pos.forEach((x, i) => (row[x] = vel[i]))
  return row
}

describe('level 1 with p = 0 matches Python exactly', () => {
  it('ring road: every position and speed of every step', () => {
    let pos = Int32Array.from(ring.pos0)
    let vel = Int32Array.from(ring.vel0)
    for (let t = 0; t < ring.steps; t++) {
      ;({ pos, vel } = stepRing(pos, vel, ring.L, ring.vmax, ring.p, neverBrake))
      expect(Array.from(pos), `pos at step ${t + 1}`).toEqual(ring.pos[t])
      expect(Array.from(vel), `vel at step ${t + 1}`).toEqual(ring.vel[t])
    }
  })

  it('open road with alpha = 1, a bus and a red light: the whole space-time diagram', () => {
    let pos = new Int32Array(0)
    let vel = new Int32Array(0)
    for (let t = 0; t < open.steps; t++) {
      ;({ pos, vel } = stepOpen(pos, vel, open.L, open.vmax, open.p, open.alpha, open.obstacles, t, neverBrake))
      expect(spacetimeRow(pos, vel, open.L), `step ${t}`).toEqual(open.spacetime[t])
    }
  })
})

describe('level 1 with p = 0.25 agrees with E1 (Python)', () => {
  // Same setup as E1: L = 1000, 200 warm-up steps, 1000 measured steps, 10 replicas.
  // Different random numbers, so the two means are compared with their combined 95% CI.
  const csv = readFileSync(new URL('../../../results/e1/fundamental_p0.25_v5.csv', import.meta.url), 'utf8')
  const [header, ...lines] = csv.trim().split('\n')
  const cols = header.split(',')
  const e1 = lines.map((l) => Object.fromEntries(l.split(',').map((v, i) => [cols[i], Number(v)])))

  for (const rho of [0.1, 0.2, 0.4]) {
    it(`mean flow at rho = ${rho}`, () => {
      const R = 10
      const flows = []
      for (let r = 0; r < R; r++) {
        const rand = mulberry32(1000 + r)
        let { pos, vel } = initRing(1000, rho, rand)
        for (let t = 0; t < 200; t++) ({ pos, vel } = stepRing(pos, vel, 1000, 5, 0.25, rand))
        let sum = 0
        for (let t = 0; t < 1000; t++) {
          ;({ pos, vel } = stepRing(pos, vel, 1000, 5, 0.25, rand))
          sum += measure(pos, vel, 1000).flow
        }
        flows.push(sum / 1000)
      }
      const mean = flows.reduce((a, b) => a + b) / R
      const sd = Math.sqrt(flows.reduce((a, b) => a + (b - mean) ** 2, 0) / (R - 1))
      const ciJs = (1.96 * sd) / Math.sqrt(R)
      const row = e1.find((x) => Math.abs(x.rho - rho) < 1e-9)
      expect(Math.abs(mean - row.q_mean)).toBeLessThan(Math.hypot(ciJs, row.q_ci95))
    })
  }
})

describe('level 1 basics', () => {
  it('the seeded generator repeats and stays in [0, 1)', () => {
    const a = mulberry32(7)
    const b = mulberry32(7)
    for (let i = 0; i < 1000; i++) {
      const x = a()
      expect(x).toBe(b())
      expect(x >= 0 && x < 1).toBe(true)
    }
  })

  it('initRing places distinct sorted cars', () => {
    const { pos, vel } = initRing(300, 0.15, mulberry32(1))
    expect(pos.length).toBe(45)
    expect(new Set(pos).size).toBe(45)
    expect(Array.from(pos)).toEqual(Array.from(pos).sort((x, y) => x - y))
    expect(vel.every((v) => v === 0)).toBe(true)
  })

  it('a permanent obstacle stops every car behind it', () => {
    let pos = new Int32Array(0)
    let vel = new Int32Array(0)
    const rand = mulberry32(3)
    const obstacles = [{ cell: 50, tStart: 0, tEnd: Infinity }]
    for (let t = 0; t < 300; t++) {
      ;({ pos, vel } = stepOpen(pos, vel, 80, 3, 0.25, 0.8, obstacles, t, rand))
      expect(pos.every((x) => x < 50)).toBe(true)
    }
    expect(pos.length).toBe(50) // the queue fills every cell behind the bus
  })
})
