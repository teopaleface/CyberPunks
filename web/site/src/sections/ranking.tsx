import { Reveal } from "@/components/reveal"
import { ApprovedCounter, QueueTable } from "@/components/ranking-board"
import { Screen } from "@/components/section-snap"
import { DB } from "@/data/daybreak"
import { fmt } from "@/lib/utils"

export function Ranking() {
  return (
    <Screen id="om" label="Decide un om">
      <div className="container-page grid gap-10 lg:grid-cols-12 lg:items-center">
        <div className="lg:col-span-5">
          <Reveal>
            <h2 className="h-section">Când nu e sigur, decide un om</h2>
          </Reveal>
          <Reveal delay={0.06}>
            <p className="mt-5 max-w-[46ch] text-white/90 lg:text-lg">
              {fmt(DB.summary.human_review)} cazuri din plan au rămas la dispecer: modelul nu e sigur, zona iese din ce a
              văzut la antrenare, sau echipele din regiune sunt deja ocupate. Agentul spune de ce.
            </p>
          </Reveal>
          <Reveal delay={0.12} className="mt-[clamp(20px,4vh,40px)]">
            <ApprovedCounter />
          </Reveal>
        </div>
        <Reveal delay={0.08} className="lg:col-span-7">
          <QueueTable limit={4} />
        </Reveal>
      </div>
    </Screen>
  )
}
