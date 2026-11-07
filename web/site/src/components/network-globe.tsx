import { Globe, type Arc, type Marker } from "@/components/ui/cobe-globe"
import { PPC_COUNTRIES, countryDots } from "@/lib/ppc-countries"
import { cn } from "@/lib/utils"

const AMBER: [number, number, number] = [1, 0.773, 0.008]
const MAGENTA: [number, number, number] = [1, 0.361, 1]
const BASE: [number, number, number] = [0.3, 0.3, 0.32]
const GLOW: [number, number, number] = [0.42, 0.12, 0.38]

/** The three countries where PPC distributes power; the other four are shown in the second colour. */
const PPC = new Set(["ro", "gr", "mk"])

/**
 * A few coloured dots over each highlighted country, sitting in the dotted
 * world like the map's own dots (no filled shapes, no chips over the map);
 * no legend, the colours speak through the page text.
 */
const MARKERS: Marker[] = countryDots(0.55).map((d, i) => ({
  id: `${d.country}-${i}`,
  location: d.location,
  size: 0.007,
  color: PPC.has(d.country) ? AMBER : MAGENTA,
}))

const cap = (id: string) => {
  const c = PPC_COUNTRIES.find((x) => x.id === id)!.capital
  return [c.lat, c.lng] as [number, number]
}

const ARCS: Arc[] = [
  { id: "ro-gr", from: cap("ro"), to: cap("gr") },
  { id: "gr-mk", from: cap("gr"), to: cap("mk") },
  { id: "mk-ro", from: cap("mk"), to: cap("ro") },
]

/** cobe's rotation that brings longitude 19° E (the middle of the seven countries) to the front. */
const PHI_EUROPE = Math.PI - ((19 * Math.PI) / 180 - Math.PI / 2)

export function NetworkGlobe({ className }: { className?: string }) {
  return (
    <figure className={cn("mx-auto w-full", className)}>
      <Globe
        markers={MARKERS}
        arcs={ARCS}
        className="w-full"
        markerColor={AMBER}
        arcColor={AMBER}
        baseColor={BASE}
        glowColor={GLOW}
        dark={1}
        diffuse={1.2}
        mapBrightness={2.6}
        mapSamples={60000}
        markerSize={0.007}
        markerElevation={0.002}
        arcWidth={0.5}
        arcHeight={0.06}
        initialPhi={PHI_EUROPE}
        theta={0.78}
        scale={2.5}
        speed={0}
      />
    </figure>
  )
}
