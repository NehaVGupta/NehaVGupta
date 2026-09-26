import { describe, expect, it } from 'vitest'
import { confidenceTier, formatConfidence } from './formatConfidence'
import { bboxToBounds, toLatLng, pixelToGeo } from './coordinates'

describe('formatConfidence', () => {
  it('formats percentages', () => { expect(formatConfidence(0.913)).toBe('91%'); expect(formatConfidence(null)).toBe('—') })
  it('applies the 80/60 tiers', () => {
    expect(confidenceTier(0.8)).toBe('high'); expect(confidenceTier(0.79)).toBe('moderate'); expect(confidenceTier(0.59)).toBe('insufficient')
  })
})

describe('coordinates', () => {
  it('flips y for Leaflet simple CRS', () => { expect(toLatLng([10, 20], 100)).toEqual([80, 10]) })
  it('converts bbox to bounds', () => { expect(bboxToBounds([10, 20, 30, 40], 100)).toEqual([[60, 10], [80, 30]]) })
  it('interpolates geographic coordinates and falls back to null', () => {
    const geo = { bounds: [0, 0, 10, 10] }
    expect(pixelToGeo(geo, 100, 100, 50, 50)).toEqual([5, 5]); expect(pixelToGeo(null, 100, 100, 1, 1)).toBeNull()
  })
})
