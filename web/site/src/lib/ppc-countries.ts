/**
 * The three countries where PPC runs distribution: Greece, Romania (Rețele
 * Electrice) and North Macedonia. Outlines are simplified by hand (about
 * 10–20 km off at the borders), enough to fill each country with dots on
 * the globe. Points are [longitude, latitude].
 */
type Ring = [number, number][]

export interface Country {
  id: string
  name: string
  capital: { name: string; lat: number; lng: number }
  /** Where the name sits: an edge of the country, so the three names never overlap. */
  labelAt: [number, number]
  rings: Ring[]
}

export const PPC_COUNTRIES: Country[] = [
  {
    id: "ro",
    name: "România",
    capital: { name: "București", lat: 44.43, lng: 26.1 },
    labelAt: [48.9, 26.2],
    rings: [
      [
        [20.26, 46.11], [21.0, 46.75], [21.6, 47.4], [22.1, 47.95], [23.0, 48.0], [24.0, 47.95], [24.9, 47.73],
        [25.9, 47.97], [26.62, 48.26], [27.5, 47.5], [28.1, 46.9], [28.2, 46.0], [28.2, 45.5], [29.6, 45.4],
        [29.7, 45.15], [28.8, 44.9], [28.65, 44.3], [28.58, 43.75], [27.9, 44.0], [27.0, 44.15], [26.1, 43.98],
        [25.0, 43.7], [23.7, 43.8], [22.9, 43.85], [22.5, 44.2], [22.0, 44.6], [21.4, 44.8], [21.4, 45.2],
        [20.7, 45.5], [20.26, 46.11],
      ],
    ],
  },
  {
    id: "gr",
    name: "Grecia",
    capital: { name: "Atena", lat: 37.98, lng: 23.73 },
    labelAt: [36.9, 19.6],
    rings: [
      [
        [20.0, 39.69], [20.6, 40.1], [20.98, 40.85], [21.9, 41.1], [22.7, 41.15], [23.6, 41.35], [24.4, 41.55],
        [25.3, 41.25], [26.1, 41.33], [26.6, 41.6], [26.0, 40.8], [25.0, 40.95], [24.0, 40.75], [23.7, 40.2],
        [22.9, 40.55], [22.6, 40.0], [23.3, 39.2], [22.9, 38.8], [23.6, 38.4], [24.1, 38.1], [23.9, 37.6],
        [23.2, 37.95], [23.1, 37.4], [22.9, 36.5], [22.4, 36.5], [21.7, 36.8], [21.5, 37.6], [21.9, 38.3],
        [21.1, 38.4], [20.7, 39.0], [20.2, 39.4], [20.0, 39.69],
      ],
      // Crete
      [[23.5, 35.3], [24.3, 35.35], [25.5, 35.3], [26.3, 35.2], [26.2, 35.0], [24.7, 34.95], [23.5, 35.2], [23.5, 35.3]],
    ],
  },
  {
    id: "mk",
    name: "Macedonia de Nord",
    capital: { name: "Skopje", lat: 42.0, lng: 21.43 },
    labelAt: [42.6, 18.6],
    rings: [
      [
        [20.45, 41.5], [20.6, 41.9], [21.0, 42.2], [21.6, 42.25], [22.4, 42.32], [22.9, 42.0], [23.0, 41.6],
        [22.7, 41.15], [22.0, 41.13], [21.3, 40.9], [20.95, 40.9], [20.5, 41.1], [20.45, 41.5],
      ],
    ],
  },
  {
    id: "bg",
    name: "Bulgaria",
    capital: { name: "Sofia", lat: 42.7, lng: 23.32 },
    labelAt: [42.7, 25.5],
    rings: [
      [
        [22.4, 44.0], [22.9, 43.85], [23.7, 43.8], [25.0, 43.7], [26.1, 43.98], [27.0, 44.15], [27.9, 44.0],
        [28.58, 43.75], [28.0, 43.2], [27.9, 42.7], [28.0, 42.0], [27.0, 42.1], [26.1, 41.33], [25.3, 41.25],
        [24.4, 41.55], [23.6, 41.35], [22.9, 41.4], [22.9, 42.0], [22.4, 42.32], [22.5, 42.9], [22.9, 43.3], [22.4, 44.0],
      ],
    ],
  },
  {
    id: "hr",
    name: "Croația",
    capital: { name: "Zagreb", lat: 45.81, lng: 15.98 },
    labelAt: [45.5, 16.4],
    rings: [
      [
        [13.5, 45.5], [14.5, 45.6], [15.6, 46.2], [16.6, 46.45], [17.6, 45.95], [18.9, 45.9], [19.4, 45.2],
        [19.0, 44.85], [17.6, 45.1], [16.0, 45.2], [15.8, 44.7], [16.4, 43.95], [17.6, 43.1], [18.5, 42.45],
        [17.0, 43.0], [15.9, 43.5], [15.2, 44.2], [14.5, 45.2], [13.6, 45.1], [13.5, 45.5],
      ],
    ],
  },
  {
    id: "it",
    name: "Italia",
    capital: { name: "Roma", lat: 41.9, lng: 12.5 },
    labelAt: [42.5, 12.5],
    rings: [
      [
        [7.0, 44.0], [6.7, 45.0], [7.0, 45.9], [8.5, 46.4], [10.2, 46.6], [12.2, 47.0], [13.7, 46.5], [13.8, 45.6],
        [12.4, 45.4], [12.3, 44.6], [13.6, 43.5], [14.0, 42.5], [15.9, 41.9], [16.1, 41.4], [18.5, 40.1], [17.0, 40.4],
        [16.5, 39.6], [17.1, 39.0], [16.2, 38.0], [15.6, 38.0], [15.9, 39.5], [15.0, 40.2], [14.0, 41.0], [12.6, 41.5],
        [11.1, 42.4], [10.5, 43.0], [10.2, 43.9], [8.8, 44.4], [7.8, 43.8], [7.0, 44.0],
      ],
      // Sicily
      [[12.4, 37.8], [13.4, 38.2], [15.6, 38.3], [15.1, 37.5], [15.1, 36.7], [14.3, 37.0], [12.5, 37.6], [12.4, 37.8]],
      // Sardinia
      [[8.4, 39.0], [8.4, 40.4], [8.2, 41.0], [9.2, 41.2], [9.8, 40.9], [9.7, 39.2], [9.0, 39.0], [8.4, 39.0]],
    ],
  },
  {
    id: "pl",
    name: "Polonia",
    capital: { name: "Varșovia", lat: 52.23, lng: 21.01 },
    labelAt: [52.2, 19.4],
    rings: [
      [
        [14.2, 53.9], [16.0, 54.3], [18.6, 54.5], [19.6, 54.4], [22.8, 54.35], [23.5, 53.9], [23.9, 52.7], [23.2, 52.3],
        [24.1, 50.8], [22.6, 49.1], [21.0, 49.4], [19.4, 49.6], [18.8, 49.5], [17.9, 50.0], [16.6, 50.4], [16.1, 50.6],
        [15.0, 51.0], [14.6, 51.8], [14.7, 52.7], [14.2, 53.9],
      ],
    ],
  },
]

function inside([x, y]: [number, number], ring: Ring) {
  let hit = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i],
      [xj, yj] = ring[j]
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) hit = !hit
  }
  return hit
}

/** Dots on a regular grid inside each country, as [lat, lng]. */
export function countryDots(step = 0.32): { country: string; location: [number, number] }[] {
  const dots: { country: string; location: [number, number] }[] = []
  for (const c of PPC_COUNTRIES) {
    for (const ring of c.rings) {
      const xs = ring.map((p) => p[0]),
        ys = ring.map((p) => p[1])
      for (let lat = Math.min(...ys); lat <= Math.max(...ys); lat += step) {
        // shift every other row half a step, so the fill reads as a weave, not a grid
        const off = Math.round((lat - Math.min(...ys)) / step) % 2 ? step / 2 : 0
        for (let lng = Math.min(...xs) + off; lng <= Math.max(...xs); lng += step) {
          if (inside([lng, lat], ring)) dots.push({ country: c.id, location: [lat, lng] })
        }
      }
    }
  }
  return dots
}
