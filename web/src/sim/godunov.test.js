// The JavaScript Godunov port against Python (fixture from experiments/export_fixtures.py).
import { describe, expect, it } from 'vitest'
import { cflDt, diagramForP, godunovStep, godunovStepRing, greenshields, measuredDiagram } from './godunov.js'
import fix from './__fixtures__/godunov_rarefaction.json'
import p0 from '../../public/fundamental_p0_v5.json'
import p01 from '../../public/fundamental_p0.1_v5.json'

describe('level 2 matches Python', () => {
  it('red light turning green (M4): same profile and same L1 error as Python', () => {
    const { Q, rhoC, qMax } = greenshields(fix.vf)
    let rho = Float64Array.from(fix.rho0)
    for (let k = 0; k < fix.steps; k++) rho = godunovStep(rho, Q, rhoC, fix.dt, fix.dx, 0, qMax)
    rho.forEach((r, i) => expect(r).toBeCloseTo(fix.rhoT[i], 12))

    const exact = fix.x.map((x) => 0.5 * (1 - Math.min(1, Math.max(-1, x / (fix.vf * fix.T)))))
    const l1 = rho.reduce((s, r, i) => s + Math.abs(r - exact[i]) * fix.dx, 0)
    expect(l1).toBeCloseTo(fix.l1, 10) // ≈ 0.95
  })
})

describe('level 2 basics', () => {
  it('cflDt', () => {
    expect(cflDt(1, 5)).toBeCloseTo(0.18)
  })

  it('the ring conserves mass', () => {
    const { Q, rhoC } = greenshields(1)
    let rho = Float64Array.from({ length: 100 }, (_, i) => 0.5 + 0.4 * Math.sin(i / 7))
    const mass = rho.reduce((a, b) => a + b)
    for (let k = 0; k < 500; k++) rho = godunovStepRing(rho, Q, rhoC, 0.9, 1)
    expect(rho.reduce((a, b) => a + b)).toBeCloseTo(mass, 9)
  })

  it('a blocked interface lets nothing through', () => {
    const { Q, rhoC } = greenshields(1)
    const cap = new Float64Array(11).fill(Infinity)
    cap[5] = 0
    let rho = new Float64Array(10)
    for (let k = 0; k < 200; k++) rho = godunovStep(rho, Q, rhoC, 0.9, 1, 0.2, 0.25, cap)
    expect(rho.slice(5).every((r) => r === 0)).toBe(true)
    expect(rho[4]).toBeGreaterThan(0.5)
  })

  it('measured diagram: ends at zero, peak from the table', () => {
    const d = measuredDiagram(p0.rows.map((r) => ({ rho: r.rho, q: r.q })))
    expect(d.Q(0)).toBe(0)
    expect(d.Q(1)).toBe(0)
    expect(d.rhoC).toBeCloseTo(1 / 6, 1) // p = 0, vmax = 5: rho_c = 1/(vmax+1)
  })

  it('diagramForP reproduces measured p and interpolates between them', () => {
    const tables = { 0: p0.rows, 0.1: p01.rows }
    const a = diagramForP(tables, 0)
    const mid = diagramForP(tables, 0.05)
    const b = diagramForP(tables, 0.1)
    expect(a.exact && b.exact).toBe(true)
    expect(mid.qMax).toBeLessThan(a.qMax)
    expect(mid.qMax).toBeGreaterThan(b.qMax)
  })
})
