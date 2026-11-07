import { Reveal } from "@/components/reveal"
import { ApprovedCounter, QueueTable } from "@/components/ranking-board"
import { Screen } from "@/components/section-snap"
import { DB } from "@/data/daybreak"
import { fmt } from "@/lib/utils"

export function Ranking() {
  return (
    <Screen id="om" label="Human review">
      <div className="container-page grid gap-10 lg:grid-cols-12 lg:items-center">
        <div className="lg:col-span-5">
          <Reveal>
            <h2 className="h-section">Uncertain cases go to a dispatcher</h2>
          </Reveal>
          <Reveal delay={0.06}>
            <p className="mt-5 max-w-[46ch] text-foreground/90 lg:text-lg">
              {fmt(DB.summary.human_review)} cases require dispatcher review because of model uncertainty, unfamiliar
              conditions or limited crew capacity. Each case includes a reason.
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
