import { describe, expect, it } from 'vitest'
import { bearingDeg, buildCellTable, distanceM } from './road.js'

describe('road geometry', () => {
  it('measures 0.01 degrees of latitude as about 1112 m', () => {
    expect(distanceM([0, 0], [0, 0.01])).toBeCloseTo(1111.95, 0)
  })

  it('computes compass bearings', () => {
    expect(bearingDeg([0, 0], [0, 1])).toBeCloseTo(0, 6) // north
    expect(bearingDeg([0, 0], [1, 0])).toBeCloseTo(90, 6) // east
    expect(bearingDeg([0, 0], [-1, 0])).toBeCloseTo(270, 6) // west
  })

  it('places one cell every 7.5 m along the line', () => {
    const { lengthM, cells } = buildCellTable([[0, 0], [0, 0.01]])
    expect(cells).toHaveLength(Math.floor(lengthM / 7.5))
    expect(distanceM([0, 0], [cells[0].lng, cells[0].lat])).toBeCloseTo(3.75, 2)
    expect(distanceM([cells[0].lng, cells[0].lat], [cells[1].lng, cells[1].lat])).toBeCloseTo(7.5, 2)
    expect(cells[10].bearing).toBeCloseTo(0, 6)
  })

  it('follows a bend: cells after the corner point east', () => {
    const { cells } = buildCellTable([[0, 0], [0, 0.001], [0.001, 0.001]])
    expect(cells[0].bearing).toBeCloseTo(0, 3)
    expect(cells[cells.length - 1].bearing).toBeCloseTo(90, 1)
  })
})
