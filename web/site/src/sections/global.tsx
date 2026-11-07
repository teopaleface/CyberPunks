import { NetworkGlobe } from "@/components/network-globe"
import { Reveal } from "@/components/reveal"
import { Screen } from "@/components/section-snap"
import { SITE } from "@/lib/site"

export const NEEDS = [
  {
    t: "Contoarele și contorul postului",
    d: "Consumul la 15 minute. Unde postul n-are contor de bilanț, energia intrată se estimează din clienți și din modelul rețelei.",
  },
  {
    t: "Vremea",
    d: "Prognoza publică pe zone. Modelul de furtună a învățat din avarii reale (EAGLE-I) și vreme istorică (Open-Meteo).",
  },
  {
    t: "Rețeaua și echipele",
    d: "Posturile, clienții de sub ele, bazele și echipele cu abilitățile și turele lor.",
  },
]

export function Global() {
  return (
    <Screen id="global" label="Aceeași regulă, în trei țări" className="overflow-hidden">
      <div className="container-page grid items-center gap-10 lg:grid-cols-12">
        <div className="lg:col-span-6">
          <Reveal>
            <h2 className="h-section">Aceeași regulă, în trei țări</h2>
          </Reveal>
          <Reveal delay={0.06}>
            <p className="mt-5 max-w-[48ch] text-white/90 lg:text-lg">
              PPC distribuie energie în România (Rețele Electrice: Muntenia Sud, Dobrogea, Banat), în Grecia și în
              Macedonia de Nord. {SITE.name} folosește doar date pe care fiecare distribuitor le are deja, așa că
              aceeași regulă merge în toate trei.
            </p>
          </Reveal>
          <ul className="mt-[clamp(20px,4vh,40px)] space-y-5">
            {NEEDS.map((n, i) => (
              <Reveal as="li" key={n.t} delay={0.1 + i * 0.05} className="flex gap-5">
                <span aria-hidden className="mt-1.5 h-7 w-1 shrink-0 rounded-full bg-ember" />
                <div>
                  <h3 className="font-sans text-lg font-semibold tracking-[-0.01em]">{n.t}</h3>
                  <p className="mt-1 text-white/80">{n.d}</p>
                </div>
              </Reveal>
            ))}
          </ul>
        </div>
        <Reveal delay={0.08} className="lg:col-span-6">
          <NetworkGlobe className="max-w-[min(580px,68vh)]" />
        </Reveal>
      </div>
    </Screen>
  )
}
