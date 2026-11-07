import { Reveal } from "@/components/reveal"
import { Screen } from "@/components/section-snap"
import { DB } from "@/data/daybreak"
import { cn, fmt } from "@/lib/utils"

export const TO_CONFIRM = [
  "Există contor de bilanț în posturi, și la ce procent dintre ele? Concentratorul de date din post nu este același lucru.",
  "Lista client → post este de încredere?",
  "Unde nu există contor de bilanț, estimăm energia intrată în post din clienți și din modelul rețelei, și recomandăm unde merită montat primul contor.",
]

const pct = (v: number) => `${fmt(v * 100, 1)}%`

/** The agent against simple strategies, from the team's evaluation script. */
export function EvalTable() {
  return (
    <table data-ui className="w-full text-left">
      <thead>
        <tr className="text-sm text-white/65">
          <th className="pb-3 font-normal">Strategie</th>
          <th className="pb-3 text-right font-normal">Valoare netă pe zi</th>
          <th className="hidden pb-3 text-right font-normal md:table-cell">Km pe zi</th>
          <th className="pb-3 text-right font-normal">Vizite degeaba</th>
          <th className="hidden pb-3 text-right font-normal md:table-cell">Furtuni acoperite</th>
        </tr>
      </thead>
      <tbody className="tabular">
        {DB.evaluation.rows.map((r) => {
          const agent = r.key === "agent"
          return (
            <tr key={r.key} className={cn("border-t border-white/10", agent && "bg-white/[0.04]")}>
              <td className={cn("py-3.5 pr-4", agent ? "font-semibold" : "text-white/85")}>{r.name}</td>
              <td className={cn("py-3.5 text-right", agent && "font-semibold text-ember-soft")}>{fmt(r.netLeiDay)} lei</td>
              <td className="hidden py-3.5 text-right text-white/85 md:table-cell">{fmt(r.kmDay)}</td>
              <td className="py-3.5 text-right text-white/85">{pct(r.uselessRate)}</td>
              <td className="hidden py-3.5 text-right text-white/85 md:table-cell">
                {r.stormsCovered} din {r.stormsTotal}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

export function agentGain() {
  const rows = DB.evaluation.rows
  const agent = rows.find((r) => r.key === "agent")!
  const best = rows.filter((r) => r.key !== "agent").sort((a, b) => b.netLeiDay - a.netLeiDay)[0]
  return { gain: Math.round((agent.netLeiDay / best.netLeiDay - 1) * 100), best }
}

export function Demo() {
  const { gain, best } = agentGain()
  return (
    <Screen id="masurat" label="Măsurat față de strategii simple">
      <div className="container-page grid gap-10 lg:grid-cols-12 lg:items-center">
        <div className="lg:col-span-5">
          <Reveal>
            <h2 className="h-section">Măsurat, nu promis</h2>
          </Reveal>
          <Reveal delay={0.06}>
            <p className="mt-5 max-w-[44ch] text-white/90 lg:text-lg">
              Pe {DB.evaluation.days} de zile într-o lume sintetică, cu adevărul cunoscut, agentul aduce mai multă valoare
              netă decât cea mai bună strategie simplă ({best.name.toLowerCase()}):
            </p>
          </Reveal>
          <Reveal delay={0.1}>
            <p className="tabular mt-6 text-[clamp(2.6rem,min(5vw,8vh),4.6rem)] leading-none font-semibold tracking-[-0.03em]">
              +{gain}%
            </p>
          </Reveal>
        </div>
        <Reveal delay={0.08} className="lg:col-span-7">
          <div className="rounded-2xl bg-surface p-[clamp(20px,2.6vw,36px)]">
            <EvalTable />
            <p className="mt-5 text-sm text-white/60">
              Generat de scriptul de evaluare al echipei, cu aceleași reguli și același planificator. Lume sintetică.
            </p>
          </div>
        </Reveal>
      </div>
    </Screen>
  )
}
