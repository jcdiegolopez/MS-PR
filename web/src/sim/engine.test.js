import { describe, expect, it } from 'vitest'
import { addBus, carsAt, createSim, lightIsRed, stepSim } from './engine.js'
import { greenshields } from './godunov.js'

const diagram = greenshields(1)
const base = { rho: 0.15, alpha: 0.3, vmax: 5, p: 0.25, seed: 3, red: 30, green: 30 }

describe('viewer engine', () => {
  it('ring: car identities follow the cars across the wrap', () => {
    const sim = createSim({ ...base, scenario: 'ring' }, 200, diagram)
    for (let t = 0; t < 300; t++) {
      const before = new Map(sim.ids.map((id, i) => [id, sim.pos[i]]))
      stepSim(sim)
      sim.ids.forEach((id, i) => {
        const moved = (sim.pos[i] - before.get(id) + 200) % 200
        expect(moved).toBe(sim.vel[i]) // each id moved exactly its own speed
      })
    }
  })

  it('ring: the macro level keeps its mass (no cars appear or vanish)', () => {
    const sim = createSim({ ...base, scenario: 'ring' }, 200, diagram)
    const mass = sim.rho.reduce((a, b) => a + b)
    for (let t = 0; t < 100; t++) stepSim(sim)
    expect(sim.rho.reduce((a, b) => a + b)).toBeCloseTo(mass, 8)
  })

  it('open road: ids survive insertions and exits', () => {
    const sim = createSim({ ...base, scenario: 'bus' }, 150, diagram)
    for (let t = 0; t < 200; t++) {
      const before = new Map(sim.ids.map((id, i) => [id, sim.pos[i]]))
      stepSim(sim)
      sim.ids.forEach((id, i) => {
        if (before.has(id)) expect(sim.pos[i] - before.get(id)).toBe(sim.vel[i])
      })
    }
    expect(sim.pos.length).toBeGreaterThan(4) // the warm-up filled the road (~0.3 cars/step at speed 5)
  })

  it('a bus stops traffic behind it for 30 s, then disappears', () => {
    const sim = createSim({ ...base, scenario: 'bus' }, 150, diagram)
    addBus(sim, 100)
    const behind = new Set(sim.ids.filter((_, i) => sim.pos[i] < 100))
    for (let t = 0; t < 30; t++) {
      stepSim(sim)
      sim.ids.forEach((id, i) => {
        if (behind.has(id)) expect(sim.pos[i]).toBeLessThan(100) // nobody behind the bus gets past it
      })
    }
    stepSim(sim)
    expect(sim.ids.some((id, i) => behind.has(id) && sim.pos[i] >= 100 - 5)).toBe(true) // traffic resumes
    expect(sim.buses).toHaveLength(0)
  })

  it('traffic light alternates red and green', () => {
    const sim = createSim({ ...base, scenario: 'light' }, 150, diagram)
    expect(lightIsRed(sim, 0)).toBe(true)
    expect(lightIsRed(sim, 29)).toBe(true)
    expect(lightIsRed(sim, 30)).toBe(false)
    expect(lightIsRed(sim, 60)).toBe(true)
  })

  it('carsAt interpolates between steps', () => {
    const sim = createSim({ ...base, scenario: 'ring', p: 0 }, 200, diagram)
    for (let t = 0; t < 20; t++) stepSim(sim)
    const a = carsAt(sim, 0)
    const b = carsAt(sim, 1)
    b.forEach((car, i) => expect(car.x).toBeCloseTo(sim.pos[i], 9))
    a.forEach((car) => expect(car.x).toBe(sim.prev.get(car.id)))
  })
})
