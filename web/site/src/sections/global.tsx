import { NetworkGlobe } from "@/components/network-globe"
import { Reveal } from "@/components/reveal"
import { Screen } from "@/components/section-snap"

export function Global() {
  return (
    <Screen id="global" label="O singură soluție pentru 3 țări" className="overflow-hidden">
      <div className="container-page grid items-center gap-10 lg:grid-cols-12">
        <div className="lg:col-span-6">
          <Reveal>
            <h2 className="h-section">O singură soluție pentru 3 țări</h2>
          </Reveal>
        </div>
        <Reveal delay={0.08} className="lg:col-span-6">
          <NetworkGlobe className="max-w-[min(580px,68vh)]" />
        </Reveal>
      </div>
    </Screen>
  )
}
