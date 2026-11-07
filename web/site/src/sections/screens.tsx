import { Reveal } from "@/components/reveal"
import { Screen } from "@/components/section-snap"
import { TiltedGrid } from "@/components/ui/tilted-grid"
import { DB, DIAGNOSIS_RO, SOURCES, type SourceKey } from "@/data/daybreak"
import { fmt, lei } from "@/lib/utils"

function Frame({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div data-ui className="h-[280px] overflow-hidden rounded-2xl bg-[#0e0e10]">
      <div className="flex items-center gap-2 px-4 pt-3.5 pb-2 text-[13px] text-white/75">
        <span className="size-2 rounded-full bg-ember" />
        {title}
      </div>
      <div className="h-[calc(100%-40px)] px-4 pb-4">{children}</div>
    </div>
  )
}

const COLOR = { verde: "#4ade80", galben: "#ffc502", rosu: "#ffc502" } as const

/** The 300 transformer posts of the plan, projected onto the tile. */
function MapTile() {
  const pts = DB.posts
  const lats = pts.map((p) => p.lat),
    lngs = pts.map((p) => p.lng)
  const [a, b, c, d] = [Math.min(...lats), Math.max(...lats), Math.min(...lngs), Math.max(...lngs)]
  const x = (lng: number) => 10 + ((lng - c) / (d - c)) * 330
  const y = (lat: number) => 230 - ((lat - a) / (b - a)) * 220
  return (
    <svg viewBox="0 0 350 240" className="h-full w-full" role="img" aria-label="Posturile de transformare, colorate după pierdere">
      {pts
        .slice()
        .sort((p, q) => (p.color === "verde" ? -1 : 0) - (q.color === "verde" ? -1 : 0))
        .map((p) => (
          <circle key={p.id} cx={x(p.lng)} cy={y(p.lat)} r={p.color === "verde" ? 2.2 : 3.6} fill={COLOR[p.color]} opacity={p.color === "verde" ? 0.55 : 1} />
        ))}
    </svg>
  )
}

function PostTile() {
  const c = DB.cases[2]
  return (
    <div className="flex h-full flex-col">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <span className="truncate font-medium">{c.label.replace(" (sintetic)", "")}</span>
        <span className="tabular shrink-0 text-sm">{lei(c.lossLeiMonth ?? 0)}/lună</span>
      </div>
      <ul className="space-y-2">
        {Object.entries(c.proba)
          .sort((p, q) => q[1] - p[1])
          .slice(0, 4)
          .map(([k, v]) => (
            <li key={k}>
              <div className="flex justify-between text-[13px] text-white/80">
                <span>{DIAGNOSIS_RO[k]}</span>
                <span className="tabular">{fmt(v * 100)}%</span>
              </div>
              <span className="mt-1 block h-1.5 rounded-full bg-white/10">
                <span className={k === c.diagnosis ? "block h-full rounded-full bg-ember" : "block h-full rounded-full bg-white/45"} style={{ width: `${v * 100}%` }} />
              </span>
            </li>
          ))}
      </ul>
      <p className="mt-auto text-[13px] text-white/70">{c.decisionRo}{c.crew ? `, echipa ${c.crew}` : ""}</p>
    </div>
  )
}

function CrewsTile() {
  return (
    <ul className="space-y-1.5">
      {DB.routes.slice(0, 6).map((r) => {
        const src = (Object.keys(r.sources)[0] as SourceKey) ?? "A"
        return (
          <li key={r.crew} className="flex items-center justify-between gap-3 rounded-lg bg-white/[0.04] px-3 py-2 text-sm">
            <span className="flex items-center gap-2 font-medium">
              <span className="size-2 rounded-full" style={{ background: SOURCES[src].color }} />
              {r.crew}
            </span>
            <span className="tabular text-white/75">
              {r.back ? `${r.depart}–${r.back}` : `de la ${r.depart}`}, {r.stops === 1 ? "1 oprire" : `${r.stops} opriri`}
            </span>
          </li>
        )
      })}
    </ul>
  )
}

function ValueTile() {
  return (
    <div className="flex h-full flex-col justify-between">
      <div>
        <div className="tabular text-5xl font-semibold tracking-tight">
          {fmt(DB.summary.expected_value_lei)} <span className="text-2xl text-white/80">lei</span>
        </div>
        <div className="mt-1 text-sm text-white/70">valoare așteptată a planului</div>
      </div>
      <ul className="space-y-1 text-sm text-white/80">
        <li className="tabular">{fmt(DB.summary.assigned)} lucrări la echipe</li>
        <li className="tabular">{fmt(DB.summary.remote_actions)} verificări de la distanță</li>
        <li className="tabular">{fmt(DB.summary.human_review)} cazuri la un om</li>
      </ul>
    </div>
  )
}

const SCREENS = [
  {
    title: "Harta posturilor",
    body: "Cele 300 de posturi, colorate verde, galben sau roșu după câți lei se pierd acolo.",
    tile: (
      <Frame title="Harta posturilor">
        <MapTile />
      </Frame>
    ),
  },
  {
    title: "Pagina unui post",
    body: "Cauza probabilă, cât de sigur e modelul, factorii și decizia agentului.",
    tile: (
      <Frame title="Pagina unui post">
        <PostTile />
      </Frame>
    ),
  },
  {
    title: "Echipele de mâine",
    body: "Traseul fiecărei echipe, cu plecarea, întoarcerea și opririle, în limita turei.",
    tile: (
      <Frame title="Echipele de mâine">
        <CrewsTile />
      </Frame>
    ),
  },
  {
    title: "Valoarea planului",
    body: "Cât aduce planul înapoi, ca să se vadă de ce merită fiecare deplasare.",
    tile: (
      <Frame title="Valoarea planului">
        <ValueTile />
      </Frame>
    ),
  },
]

export function Screens() {
  return (
    <Screen id="ecrane" label="Patru ecrane pentru dispecer" className="overflow-hidden">
      <div className="container-page">
        <Reveal>
          <h2 className="h-section">Patru ecrane pentru dispecer</h2>
        </Reveal>
      </div>

      <Reveal delay={0.06}>
        <TiltedGrid tiles={SCREENS.map((s) => s.tile)} className="h-[clamp(320px,44vh,420px)]" tileWidth={360} />
      </Reveal>

      <div className="container-page">
        <dl className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {SCREENS.map((s, i) => (
            <Reveal key={s.title} delay={0.04 * i}>
              <dt className="font-semibold lg:text-lg">{s.title}</dt>
              <dd className="mt-1.5 text-white/85">{s.body}</dd>
            </Reveal>
          ))}
        </dl>
      </div>
    </Screen>
  )
}
