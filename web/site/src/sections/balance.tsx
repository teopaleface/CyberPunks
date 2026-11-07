import { Reveal } from "@/components/reveal"
import { Screen } from "@/components/section-snap"
import { BalanceExplorer } from "@/components/balance-explorer"

export function Balance() {
  return (
    <Screen id="bilant" label="Transformer energy balance">
      <div className="container-page">
        <div className="grid gap-6 lg:grid-cols-12 lg:items-end">
          <Reveal className="lg:col-span-6">
            <h2 className="h-section">Transformer energy balance</h2>
          </Reveal>
          <Reveal delay={0.06} className="lg:col-span-6">
            <p className="text-white/90 lg:text-lg">
              Select a transformer to see its excess loss, likely cause and planned action.
            </p>
          </Reveal>
        </div>
        <Reveal delay={0.12} className="mt-[clamp(16px,3vh,36px)]">
          <BalanceExplorer compact />
        </Reveal>
      </div>
    </Screen>
  )
}
