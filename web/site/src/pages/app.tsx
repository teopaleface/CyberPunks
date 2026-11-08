import "leaflet/dist/leaflet.css"
import {
  AlertTriangle,
  BellRing,
  BookText,
  BrainCircuit,
  CalendarClock,
  CalendarDays,
  CloudLightning,
  ClipboardList,
  Hand,
  Loader2,
  LogOut,
  Map as MapIcon,
  UserRound,
} from "lucide-react"
import { useEffect, useId, useMemo, useRef, useState, type FormEvent } from "react"
import { CircleMarker, MapContainer, Polyline, Popup, useMap } from "react-leaflet"
import { MapShell, SchematicTiles } from "@/components/map-shell"
import { Link, NavLink, Outlet, useNavigate, useParams } from "react-router-dom"
import { DECISION_TONE, outcomeOf } from "@/components/balance-explorer"
import { CrewStatusCell } from "@/components/crew-status"
import { ItemDetail, Panel } from "@/components/item-detail"
import { QueueCard, QUEUE, SourceTag } from "@/components/ranking-board"
import { GlassButton, GlassLink } from "@/components/ui/liquid-glass-button"
import { ThemedSelect } from "@/components/ui/themed-select"
import {
  BILANT_NOTE,
  DB,
  DECISION_RO,
  DIAGNOSIS_RO,
  SOURCES,
  type Decision,
  type ModelCard,
  type SourceKey,
} from "@/data/daybreak"
import { useApprovals } from "@/lib/approvals"
import { displayName, useAuth } from "@/lib/auth"
import { ROUTES } from "@/lib/site"
import { TEAMS, type Team } from "@/lib/supabase"
import { cn, fmt, lei } from "@/lib/utils"
import { EvalTable, agentGain } from "@/sections/demo"
import { MODEL_LINES } from "@/sections/how-it-works"

interface NavEntry {
  to: string
  label: string
  icon: typeof CalendarClock
  end?: boolean
}

/** Grouped by the dispatcher's day: what to do today, what is out there, and how the agent decides. */
const SIDEBAR: { group: string; items: NavEntry[] }[] = [
  {
    group: "Azi",
    items: [
      { to: "/app", label: "Planul de mâine", icon: CalendarClock, end: true },
      { to: "/app/coada", label: "Decide un om", icon: Hand },
      { to: "/app/alerte", label: "Alerte", icon: BellRing },
    ],
  },
  {
    group: "Rețeaua",
    items: [
      { to: "/app/posturi", label: "Posturi", icon: MapIcon },
      { to: "/app/lucrari", label: "Lucrări", icon: ClipboardList },
    ],
  },
  {
    group: "Cum decide",
    items: [
      { to: "/app/jurnal", label: "Jurnal", icon: BookText },
      { to: "/app/modele", label: "Modele și evaluare", icon: BrainCircuit },
    ],
  },
]

function SideLink({ to, label, icon: Icon, end }: NavEntry) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "flex h-9 items-center gap-2.5 rounded-xl px-3 text-[15px] whitespace-nowrap transition-colors duration-150",
          isActive ? "bg-white/[0.08] text-white" : "text-white/65 hover:bg-white/[0.04] hover:text-white"
        )
      }
    >
      <Icon className="size-4 shrink-0" aria-hidden />
      {label}
      {to === "/app/coada" && <QueueBadge />}
    </NavLink>
  )
}

/**
 * Workspace frame. The sidebar sits flush on the window's left edge, narrow,
 * with the product and the plan it works on at the top; the canvas takes the
 * rest of the width.
 */
/** 2025-07-08 -> 08-07-2025 */
const dmy = (iso: string) => iso.split("-").reverse().join("-")

/** The plan's day, large, with a calendar to pick another one. */
function DatePick({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const ref = useRef<HTMLInputElement>(null)
  return (
    <div className="mb-6 flex items-center justify-between gap-2 px-3 lg:-mt-2">
      <div className="tabular font-display text-[1.4rem] leading-tight font-semibold tracking-[-0.02em] whitespace-nowrap" aria-label={`Planul pentru ${dmy(value)}`}>
        {dmy(value)}
      </div>
      <label className="relative grid size-10 cursor-pointer place-items-center rounded-xl bg-white/[0.06] text-white/85 transition-colors duration-150 hover:bg-white/[0.12] hover:text-white">
        <CalendarDays className="size-5" aria-hidden />
        <span className="sr-only">Alege altă zi</span>
        <input
          ref={ref}
          type="date"
          value={value}
          max="2026-12-31"
          onChange={(e) => e.target.value && onChange(e.target.value)}
          onClick={() => ref.current?.showPicker?.()}
          className="absolute inset-0 cursor-pointer opacity-0"
        />
      </label>
    </div>
  )
}

export function AppLayout() {
  const { user, profile } = useAuth()
  const [day, setDay] = useState(DB.planDate)
  return (
    <div className="grid min-h-[100svh] pt-[clamp(88px,11vh,104px)] lg:grid-cols-[220px_minmax(0,1fr)]">
      <aside className="min-w-0 px-4 lg:sticky lg:top-[clamp(88px,11vh,104px)] lg:h-[calc(100svh-clamp(88px,11vh,104px))] lg:self-start lg:overflow-y-auto lg:pr-2 lg:pb-6">
        <DatePick value={day} onChange={setDay} />
        <nav aria-label="Servicii" className="-mx-4 overflow-x-auto px-4 lg:mx-0 lg:overflow-visible lg:px-0">
          <div className="flex gap-1 lg:flex-col lg:gap-5">
            {SIDEBAR.map((g) => (
              <div key={g.group} className="flex gap-1 lg:flex-col lg:gap-0.5">
                <div className="hidden px-3 pb-1 text-[13px] text-white/45 lg:block">{g.group}</div>
                {g.items.map((it) => (
                  <SideLink key={it.to} {...it} />
                ))}
              </div>
            ))}
          </div>
        </nav>
        <div className="mt-6 hidden lg:block">
          <SideLink to="/app/cont" label={user ? displayName(user, profile) : "Contul meu"} icon={UserRound} />
        </div>
      </aside>
      <main className="min-w-0 px-4 pt-4 pb-24 lg:pt-1 lg:pr-8 lg:pl-6">
        <div className="max-w-[1320px]">
          {day !== DB.planDate && (
            <div role="status" className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-amber/12 px-4 py-3">
              <p className="text-white/90">
                Pentru {dmy(day)} nu există încă un plan: agentul îl face în noaptea dinainte. Arătăm ultimul plan, din {dmy(DB.planDate)}.
              </p>
              <button
                type="button"
                onClick={() => setDay(DB.planDate)}
                className="cursor-pointer rounded-full bg-white/[0.08] px-4 py-2 text-sm font-medium hover:bg-white/15"
              >
                Înapoi la {dmy(DB.planDate)}
              </button>
            </div>
          )}
          <Outlet />
        </div>
      </main>
    </div>
  )
}

function QueueBadge() {
  const { decisions } = useApprovals()
  const left = QUEUE.filter((q) => !decisions.has(q.id)).length
  if (!left) return null
  return <span className="tabular ml-auto rounded-full bg-ember px-2 py-0.5 text-xs font-semibold text-black">{left}</span>
}

function Title({ children, lead }: { children: React.ReactNode; lead?: React.ReactNode }) {
  return (
    <header className="mb-8">
      <h1 className="text-[clamp(1.4rem,2vw,1.9rem)] leading-tight font-semibold">{children}</h1>
      {lead && <p className="mt-3 max-w-[70ch] text-white/85">{lead}</p>}
    </header>
  )
}

/* ---------------- Planul de mâine ---------------- */

/** First sentence of an alert's body, without the list of ids that follows a colon. */
function gist(body: string) {
  const first = body.split(/(?<=\.)\s/)[0]
  const cut = first.indexOf(": ")
  return cut > 20 ? first.slice(0, cut) + "." : first
}

const toMin = (t: string) => {
  const [h, m] = t.split(":").map(Number)
  return h * 60 + m
}

/** Tomorrow on one screen: what needs you, what the agent did today, who goes where. */
export function Overview() {
  const { decisions } = useApprovals()
  const waiting = QUEUE.filter((q) => !decisions.has(q.id))
  const waitingLei = waiting.reduce((s, q) => s + q.expectedValueLei, 0)
  const runAt = DB.generatedAt.slice(11, 16)

  // What a person must act on: reinforcements and storms; the info notes and the
  // cases that go first automatically stay out.
  const needs = DB.alerts.filter((a) => a.severity !== "info" && !/^\d+ cazuri cu risc de siguranță$/.test(a.title))
  const storms = needs.filter((a) => a.title.startsWith("Risc de avarii"))
  const others = needs.filter((a) => !a.title.startsWith("Risc de avarii"))

  const free = DB.crews.filter((c) => !DB.routes.some((r) => r.crew === c.id))
  const start = toMin(DB.shift.start),
    end = toMin("17:00")

  const S = DB.summary
  const RUN = [
    { n: S.items_in, t: "lucrări citite din contoare, vreme și rețea", strong: false },
    { n: S.remote_actions, t: "rezolvate de la distanță, fără deplasare", strong: false },
    { n: S.assigned, t: "trimise la echipe, în trasee", strong: true },
    { n: S.human_review, t: "lăsate la tine, pentru că nu e sigur", strong: true },
    { n: DB.decisionCounts.deferred ?? 0, t: "amânate: nu merită încă o deplasare", strong: false },
    { n: S.notifications, t: "notificări pregătite (demo, nu s-au trimis)", strong: false },
  ]

  return (
    <>
      <Title>Decizii în valoare de {lei(S.expected_value_lei)} te așteaptă</Title>

      <div className="grid gap-6 xl:grid-cols-12">
        <Panel title="Ce îți cere atenția mâine" className="xl:col-span-7">
          <ol className="space-y-2">
            <li>
              <Link
                to="/app/coada"
                className="group flex items-start gap-4 rounded-2xl bg-white/[0.04] p-4 transition-colors duration-150 hover:bg-white/[0.08]"
              >
                <Hand className="mt-0.5 size-5 shrink-0 text-amber" aria-hidden />
                <span className="min-w-0 flex-1">
                  <span className="block font-semibold">
                    {waiting.length ? `${waiting.length} cazuri așteaptă decizia ta` : "Ai decis toate cazurile"}
                  </span>
                  <span className="block text-white/75">
                    {waiting.length ? `Valoare așteptată ${lei(waitingLei)}. Alegi echipajul, amâni sau respingi.` : "Nimic nu mai așteaptă un om."}
                  </span>
                </span>
                <span className="shrink-0 text-sm font-medium text-white/70 group-hover:text-white">Deschide</span>
              </Link>
            </li>
            {others.map((a) => (
              <li key={a.id}>
                <Link
                  to="/app/alerte"
                  className="group flex items-start gap-4 rounded-2xl bg-white/[0.04] p-4 transition-colors duration-150 hover:bg-white/[0.08]"
                >
                  <AlertTriangle className={cn("mt-0.5 size-5 shrink-0", a.severity === "critical" ? "text-magenta" : "text-amber")} aria-hidden />
                  <span className="min-w-0 flex-1">
                    <span className="block font-semibold">{a.title}</span>
                    <span className="block text-white/75">{gist(a.body)}</span>
                  </span>
                </Link>
              </li>
            ))}
            {storms.length > 0 && (
              <li>
                <Link
                  to="/app/alerte"
                  className="group flex items-start gap-4 rounded-2xl bg-white/[0.04] p-4 transition-colors duration-150 hover:bg-white/[0.08]"
                >
                  <CloudLightning className="mt-0.5 size-5 shrink-0 text-magenta" aria-hidden />
                  <span className="min-w-0 flex-1">
                    <span className="block font-semibold">
                      Furtună în {storms.map((a) => a.title.replace("Risc de avarii: ", "").replace(/ \(.*\)$/, "")).join(" și ")}
                    </span>
                    <span className="block text-white/75">{storms[0].body.match(/Furtuna e așteptată[^.]*\./)?.[0] ?? gist(storms[0].body)}</span>
                  </span>
                </Link>
              </li>
            )}
          </ol>
        </Panel>

        <Panel title={`Rularea de azi, la ${runAt}`} className="xl:col-span-5">
          <ol className="space-y-3">
            {RUN.map((r) => (
              <li key={r.t} className="grid grid-cols-[4.5rem_1fr] items-baseline gap-3">
                <span className={cn("tabular text-right text-2xl font-semibold", r.strong ? "text-white" : "text-white/70")}>{fmt(r.n)}</span>
                <span className={r.strong ? "text-white" : "text-white/75"}>{r.t}</span>
              </li>
            ))}
          </ol>
        </Panel>

        <Panel title="Echipele de mâine" className="xl:col-span-12">
          <div className="tabular mb-2 grid grid-cols-[6.5rem_1fr_9rem] gap-3 text-sm text-white/50">
            <span />
            <span className="flex justify-between">
              {["08:00", "10:00", "12:00", "14:00", "16:00"].map((t) => (
                <span key={t}>{t}</span>
              ))}
            </span>
            <span />
          </div>
          <ul className="space-y-2" aria-label="Traseele echipelor">
            {DB.routes.map((r) => {
              const a = Math.max(0, (toMin(r.depart) - start) / (end - start))
              const b = r.back ? Math.min(1, (toMin(r.back) - start) / (end - start)) : 1
              const src = (Object.keys(r.sources)[0] as SourceKey) ?? "A"
              const crew = DB.crews.find((c) => c.id === r.crew)
              return (
                <li key={r.crew} className="grid grid-cols-[6.5rem_1fr_9rem] items-center gap-3">
                  <span>
                    <span className="block font-semibold">{r.crew}</span>
                    <span className="block text-sm text-white/55">{crew?.depotRo ?? r.depot}</span>
                  </span>
                  <span className="relative h-7 rounded-lg bg-white/[0.05]">
                    <span
                      className="absolute inset-y-0 flex items-center rounded-lg px-2 text-sm font-medium text-black"
                      style={{ left: `${a * 100}%`, width: `${(b - a) * 100}%`, background: SOURCES[src].color }}
                    >
                      <span className="truncate">{r.back ? `${r.depart}–${r.back}` : `de la ${r.depart}, în zonă`}</span>
                    </span>
                  </span>
                  <span className="tabular text-right text-sm text-white/75">
                    {r.stops === 1 ? "1 oprire" : `${r.stops} opriri`}, {fmt(r.km, 1)} km
                  </span>
                </li>
              )
            })}
          </ul>
          {free.length > 0 && (
            <p className="mt-5 text-white/85">
              <span className="font-semibold text-ok">Libere mâine:</span>{" "}
              {free.map((c) => `${c.id} (${c.depotRo})`).join(", ")}. Le poți aloca din „Decide un om”.
            </p>
          )}
        </Panel>

        <div className="xl:col-span-12">
          <PlanMap />
        </div>
      </div>
    </>
  )
}

/* ---------------- Harta ---------------- */

const DECISION_FILTERS: { key: Decision | "toate"; label: string }[] = [
  { key: "toate", label: "Toate" },
  { key: "assigned", label: "La echipe" },
  { key: "human_review", label: "Decide un om" },
  { key: "remote_action", label: "De la distanță" },
  { key: "notify", label: "Notificări" },
  { key: "deferred", label: "Amânate" },
]

const ITEM_PAGE = new Set(DB.items.map((i) => i.id))

/** All work items with the crews' routes: the agent's plan on the map. */
export function PlanMap() {
  const [sources, setSources] = useState<Record<SourceKey, boolean>>({ A: true, B: true, C: true })
  const [decision, setDecision] = useState<Decision | "toate">("toate")
  const shown = useMemo(
    () => DB.allItems.filter((r) => sources[r[1]] && (decision === "toate" || r[4] === decision)),
    [sources, decision]
  )
  const routes = useMemo(() => {
    const by: Record<string, [number, number][]> = {}
    DB.routeStops
      .slice()
      .sort((a, b) => a.seq - b.seq)
      .forEach((s) => (by[s.crew] ??= []).push([s.lat, s.lng]))
    return Object.entries(by)
  }, [])

  return (
    <Panel title="Harta planului">
      <p className="-mt-2 mb-4 max-w-[70ch] text-white/75">
        Toate cele {fmt(DB.allItems.length)} de lucrări, colorate după sursă. Liniile arată ordinea opririlor fiecărei
        echipe, nu drumul exact.
      </p>
      <div className="mb-4 flex flex-wrap items-center gap-x-6 gap-y-3">
        {(["A", "B", "C"] as SourceKey[]).map((s) => (
          <label key={s} className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={sources[s]}
              onChange={(e) => setSources((p) => ({ ...p, [s]: e.target.checked }))}
              className="size-4 cursor-pointer accent-[var(--ember)]"
            />
            <SourceTag s={s} />
          </label>
        ))}
        <div className="ml-auto">
          <ThemedSelect
            label="Decizia"
            value={decision}
            onChange={setDecision}
            options={DECISION_FILTERS.map((f) => ({ value: f.key, label: f.label }))}
          />
        </div>
      </div>
      <MapShell className="h-[clamp(380px,56vh,620px)]">
        <MapContainer bounds={[[43.7, 20.8], [46.3, 29.1]]} scrollWheelZoom={false} className="h-full w-full bg-[#1c1c1e]">
          <SchematicTiles />
          {routes.map(([crew, pts]) => (
            <Polyline key={crew} positions={pts} pathOptions={{ color: "#ffc502", weight: 2, opacity: 0.8, dashArray: "4 6" }} />
          ))}
          {shown.map(([id, src, lat, lng, dec, value, score]) => (
            <CircleMarker
              key={id}
              center={[lat, lng]}
              radius={dec === "assigned" || dec === "human_review" ? 7 : 4}
              pathOptions={{
                color: dec === "human_review" ? "#ffc502" : SOURCES[src].color,
                fillColor: SOURCES[src].color,
                fillOpacity: dec === "deferred" ? 0.35 : 0.85,
                weight: dec === "human_review" ? 3 : 1,
              }}
            >
              <Popup>
                <div className="font-sans">
                  <div className="font-semibold">
                    {SOURCES[src].name}: {id}
                  </div>
                  <div>
                    {dec ? DECISION_RO[dec] : "Fără decizie"}, {lei(value ?? 0)}, scor {fmt(score ?? 0, 2)}
                  </div>
                  {ITEM_PAGE.has(id) ? <Link to={`/app/lucrari/${id}`}>Deschide lucrarea</Link> : null}
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
        {shown.length === 0 && (
          <div className="absolute inset-0 z-[500] grid place-items-center bg-black/60">
            <p className="rounded-2xl bg-surface-2 p-4">Nicio lucrare nu se potrivește filtrelor. Bifează o sursă.</p>
          </div>
        )}
      </MapShell>
    </Panel>
  )
}

/* ---------------- Lucrări ---------------- */

export function ItemsScreen() {
  const [source, setSource] = useState<SourceKey | "toate">("toate")
  const [decision, setDecision] = useState<Decision | "toate">("toate")
  const rows = DB.items
    .filter((i) => (source === "toate" || i.source === source) && (decision === "toate" || i.decision === decision))
    .sort((a, b) => b.impact.expectedValueLei - a.impact.expectedValueLei)
  return (
    <>
      <Title lead="Fiecare lucrare are predicția, factorii, cazurile asemănătoare, decizia cu regula ei și urmărirea până la model. Aici sunt cele mai importante 67.">
        Lucrările planului
      </Title>
      <div className="mb-5 flex flex-wrap gap-4">
        <ThemedSelect
          label="Sursa"
          value={source}
          onChange={setSource}
          options={[
            { value: "toate" as const, label: "Toate" },
            ...(["A", "B", "C"] as SourceKey[]).map((k) => ({ value: k, label: SOURCES[k].name })),
          ]}
        />
        <ThemedSelect
          label="Decizia"
          value={decision}
          onChange={setDecision}
          options={DECISION_FILTERS.map((f) => ({ value: f.key, label: f.label }))}
        />
      </div>
      <Panel>
        {rows.length === 0 ? (
          <div>
            <p className="font-medium">Nicio lucrare cu aceste filtre.</p>
            <button
              type="button"
              onClick={() => {
                setSource("toate")
                setDecision("toate")
              }}
              className="mt-2 cursor-pointer underline underline-offset-4 hover:text-ember-soft"
            >
              Arată toate lucrările
            </button>
          </div>
        ) : (
          <table data-ui className="w-full text-left">
            <thead>
              <tr className="text-sm text-white/60">
                <th className="pb-3 font-normal">Lucrarea</th>
                <th className="hidden pb-3 font-normal md:table-cell">Decizia</th>
                <th className="pb-3 font-normal">Echipajul</th>
                <th className="pb-3 text-right font-normal">Scor</th>
                <th className="pb-3 text-right font-normal">Valoare</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((i) => (
                <tr key={i.id} className="border-t border-white/10 align-top">
                  <td className="py-3 pr-4">
                    <Link to={`/app/lucrari/${i.id}`} className="group block">
                      <span className="flex flex-wrap items-center gap-x-3">
                        <SourceTag s={i.source} />
                        <span className="font-medium group-hover:underline group-hover:underline-offset-4">{i.label}</span>
                      </span>
                      <span className="mt-0.5 block text-sm text-white/55">{i.id}</span>
                    </Link>
                  </td>
                  <td className={cn("hidden py-3 pr-4 md:table-cell", i.decision && DECISION_TONE[i.decision])}>
                    {i.decisionRo}
                  </td>
                  <td className="py-3 pr-4">
                    <CrewStatusCell id={i.id} />
                  </td>
                  <td className="tabular py-3 text-right">{i.prediction.score !== null ? fmt(i.prediction.score, 2) : "fără"}</td>
                  <td className="tabular py-3 text-right font-semibold">{lei(i.impact.expectedValueLei)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </>
  )
}

export function ItemScreen() {
  const { id } = useParams()
  const item = DB.items.find((i) => i.id === id)
  if (!item) {
    return (
      <>
        <Title>Lucrarea nu e în planul afișat</Title>
        <Panel>
          <p>„{id}” nu e printre lucrările păstrate pentru demo.</p>
          <Link to="/app/lucrari" className="mt-3 inline-block underline underline-offset-4 hover:text-ember-soft">
            Înapoi la lucrări
          </Link>
        </Panel>
      </>
    )
  }
  return (
    <>
      <nav aria-label="Înapoi" className="mb-4">
        <Link to="/app/lucrari" className="text-white/75 hover:text-white">
          Lucrări
        </Link>
      </nav>
      <Title>{item.label}</Title>
      <ItemDetail item={item} />
    </>
  )
}

/* ---------------- Bilanț pe post ---------------- */

const POST_COLOR = { verde: "#4ade80", galben: "#ffc502", rosu: "#ff5cff" } as const
const POST_STATUS = { verde: "În regulă", galben: "De urmărit", rosu: "Pierde peste normal" } as const
const CASE_OF_POST = new Map(DB.cases.map((c) => [c.post, c]))
const RANK = { rosu: 0, galben: 1, verde: 2 } as const

/**
 * Posts. The list is the main thing: search it, filter it, pick a post.
 * The map is a small square on the right that follows the selection, and
 * the selected post's card sits under it.
 */
export function PostsScreen() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [q, setQ] = useState("")
  const [scope, setScope] = useState<"probleme" | "toate">("probleme")
  const searchId = useId()

  const counts = DB.posts.reduce<Record<string, number>>((a, p) => ((a[p.color] = (a[p.color] ?? 0) + 1), a), {})
  const problems = (counts.rosu ?? 0) + (counts.galben ?? 0)

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return DB.posts
      .filter((p) => (scope === "toate" || p.color !== "verde") && (!needle || p.label.toLowerCase().includes(needle)))
      .sort((a, b) => RANK[a.color] - RANK[b.color] || (b.lossLeiMonth ?? 0) - (a.lossLeiMonth ?? 0))
  }, [q, scope])

  const selected = DB.posts.find((p) => p.id === id) ?? rows[0] ?? DB.posts[0]
  const pick = (post: string) => navigate(`/app/posturi/${post}`, { replace: true })
  const c = CASE_OF_POST.get(selected.id)
  const item = selected.workItem ? DB.items.find((i) => i.id === selected.workItem) : undefined

  const bounds = useMemo(() => {
    const la = DB.posts.map((p) => p.lat),
      ln = DB.posts.map((p) => p.lng)
    return [
      [Math.min(...la), Math.min(...ln)],
      [Math.max(...la), Math.max(...ln)],
    ] as [[number, number], [number, number]]
  }, [])

  return (
    <>
      <Title lead={`${counts.rosu ?? 0} pierd peste normal, ${counts.galben ?? 0} sunt de urmărit, ${counts.verde ?? 0} sunt în regulă. ${BILANT_NOTE}.`}>
        Posturile de transformare
      </Title>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        {/* the list */}
        <section aria-label="Lista posturilor" className="min-w-0">
          <div className="mb-3 flex flex-wrap items-center gap-3">
            <label htmlFor={searchId} className="sr-only">
              Caută un post
            </label>
            <input
              id={searchId}
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Caută după cod sau zonă, de exemplu Otopeni"
              className="h-10 min-w-0 flex-1 rounded-xl bg-surface-2 px-4 text-white outline-none placeholder:text-white/40 focus-visible:ring-2 focus-visible:ring-ember"
            />
            <div role="radiogroup" aria-label="Ce posturi" className="inline-flex rounded-xl bg-surface-2 p-1">
              {(
                [
                  ["probleme", `Cu probleme ${problems}`],
                  ["toate", `Toate ${DB.posts.length}`],
                ] as const
              ).map(([k, label]) => (
                <button
                  key={k}
                  type="button"
                  role="radio"
                  aria-checked={scope === k}
                  onClick={() => setScope(k)}
                  className={cn(
                    "tabular h-8 cursor-pointer rounded-lg px-3 text-sm font-medium transition-colors duration-150",
                    scope === k ? "bg-white text-black" : "text-white/75 hover:text-white"
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div data-lenis-prevent className="max-h-[calc(100svh-260px)] min-h-[320px] overflow-y-auto rounded-2xl bg-surface">
            {rows.length === 0 ? (
              <div className="p-6">
                <p className="font-medium">Niciun post nu se potrivește cu „{q}”.</p>
                <button type="button" onClick={() => setQ("")} className="mt-2 cursor-pointer underline underline-offset-4 hover:text-ember-soft">
                  Șterge căutarea
                </button>
              </div>
            ) : (
              <table className="w-full text-left">
                <thead className="sticky top-0 z-10 bg-surface">
                  <tr className="text-sm text-white/55">
                    <th className="px-4 py-3 font-normal">Post</th>
                    <th className="hidden py-3 pr-4 font-normal md:table-cell">Cauza</th>
                    <th className="py-3 pr-4 text-right font-normal whitespace-nowrap">Lei pe lună</th>
                    <th className="hidden py-3 pr-4 font-normal 2xl:table-cell">Ce facem</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((p) => {
                    const on = p.id === selected.id
                    return (
                      <tr
                        key={p.id}
                        onClick={() => pick(p.id)}
                        aria-selected={on}
                        className={cn(
                          "cursor-pointer border-t border-white/[0.06] transition-colors duration-100",
                          on ? "bg-white/[0.07]" : "hover:bg-white/[0.035]"
                        )}
                      >
                        <td className="px-4 py-2.5">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              pick(p.id)
                            }}
                            className="flex cursor-pointer items-center gap-2.5 text-left"
                          >
                            <span className="size-2.5 shrink-0 rounded-full" style={{ background: POST_COLOR[p.color] }} aria-label={POST_STATUS[p.color]} />
                            <span className={cn("font-medium whitespace-nowrap", on && "text-white")}>{p.label.replace(" (sintetic)", "")}</span>
                          </button>
                        </td>
                        <td className="hidden py-2.5 pr-4 text-[15px] text-white/80 md:table-cell">{p.diagnosis ? DIAGNOSIS_RO[p.diagnosis] : "—"}</td>
                        <td className="tabular py-2.5 pr-4 text-right font-medium whitespace-nowrap">{p.lossLeiMonth ? lei(p.lossLeiMonth) : "—"}</td>
                        <td className="hidden py-2.5 pr-4 text-[15px] whitespace-nowrap text-white/75 2xl:table-cell">{p.decision ? DECISION_RO[p.decision] : "Nimic de făcut"}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </section>

        {/* the map and the selected post */}
        <aside className="space-y-4 xl:sticky xl:top-28 xl:self-start">
          <MapShell className="aspect-square">
            <MapContainer bounds={bounds} boundsOptions={{ padding: [16, 16] }} scrollWheelZoom={false} className="h-full w-full bg-[#1c1c1e]">
              <SchematicTiles />
              <FlyTo lat={selected.lat} lng={selected.lng} />
              {(scope === "toate" ? DB.posts : DB.posts.filter((p) => p.color !== "verde")).map((p) => {
                const on = p.id === selected.id
                return (
                  <CircleMarker
                    key={p.id}
                    center={[p.lat, p.lng]}
                    radius={on ? 10 : p.color === "verde" ? 3.5 : 6}
                    eventHandlers={{ click: () => pick(p.id) }}
                    pathOptions={{
                      color: on ? "#ffffff" : POST_COLOR[p.color],
                      fillColor: POST_COLOR[p.color],
                      fillOpacity: p.color === "verde" ? 0.5 : 0.9,
                      weight: on ? 3 : 1,
                    }}
                  />
                )
              })}
            </MapContainer>
          </MapShell>

          <Panel>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-sans text-lg font-semibold tracking-[-0.01em]">{selected.label.replace(" (sintetic)", "")}</h2>
                <p className="mt-0.5 flex items-center gap-2 text-sm text-white/70">
                  <span className="size-2 rounded-full" style={{ background: POST_COLOR[selected.color] }} aria-hidden />
                  {POST_STATUS[selected.color]}, {selected.kva} kVA
                </p>
              </div>
              <div className="tabular text-right">
                <div className="text-xl font-semibold">{selected.lossLeiMonth ? lei(selected.lossLeiMonth) : "0 lei"}</div>
                <div className="text-sm text-white/60">pe lună</div>
              </div>
            </div>
            {c ? (
              <p className="mt-4 text-white/90">
                <span className="font-medium text-amber">{c.diagnosisRo}</span>, {fmt(c.score * 100)}% sigur. {outcomeOf(c).title}.
              </p>
            ) : selected.diagnosis ? (
              <p className="mt-4 text-white/90">
                <span className="font-medium text-amber">{DIAGNOSIS_RO[selected.diagnosis]}</span>
                {selected.score !== null ? `, ${fmt(selected.score * 100)}% sigur` : ""}.{" "}
                {selected.decision ? DECISION_RO[selected.decision] : ""}.
              </p>
            ) : (
              <p className="mt-4 text-white/80">Lipsa stă în banda normală. Nu trimitem pe nimeni.</p>
            )}
            {(selected.metersFlagged > 0 || selected.voltageP90) && (
              <p className="tabular mt-2 text-sm text-white/65">
                {selected.metersFlagged > 0 ? `${selected.metersFlagged} contoare semnalate` : ""}
                {selected.metersFlagged > 0 && selected.voltageP90 ? ", " : ""}
                {selected.voltageP90 ? `tensiune P90 ${fmt(selected.voltageP90, 3)} pu` : ""}
              </p>
            )}
            {item && (
              <Link to={`/app/lucrari/${item.id}`} className="mt-4 inline-block font-medium text-white underline underline-offset-4 hover:text-ember-soft">
                Vezi de ce și ce facem
              </Link>
            )}
          </Panel>
        </aside>
      </div>
    </>
  )
}

/** Keeps the small map on the selected post. */
function FlyTo({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap()
  useEffect(() => {
    map.flyTo([lat, lng], Math.max(map.getZoom(), 12), { duration: 0.6 })
  }, [lat, lng, map])
  return null
}


/* ---------------- Decide un om ---------------- */

/**
 * Decide un om: a narrow list of the cases on the left (approve, postpone or
 * reject right there), the selected case in full on the right.
 */
export function QueueScreen() {
  const { id } = useParams()
  const { decisions } = useApprovals()
  // Without a case in the address, open the first undecided one and stay on it while it is decided.
  const [first] = useState(() => (QUEUE.find((q) => !decisions.has(q.id)) ?? QUEUE[0])?.id)
  const selected = QUEUE.find((q) => q.id === (id ?? first)) ?? QUEUE[0]
  const item = selected ? DB.items.find((i) => i.id === selected.id) : undefined
  const counts = { approved: 0, deferred: 0, rejected: 0 }
  QUEUE.forEach((q) => {
    const v = decisions.get(q.id)
    if (v) counts[v]++
  })
  const waiting = QUEUE.length - counts.approved - counts.deferred - counts.rejected

  return (
    <>
      <header className="mb-6 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <h1 className="text-[clamp(1.4rem,2vw,1.9rem)] leading-tight font-semibold">Decide un om</h1>
        <p className="tabular text-white/75">
          {waiting} așteaptă, <span className="text-ok">{counts.approved} aprobate</span>,{" "}
          <span className="text-amber">{counts.deferred} amânate</span>, <span className="text-magenta">{counts.rejected} respinse</span>
        </p>
      </header>

      {QUEUE.length === 0 || !selected || !item ? (
        <Panel>
          <p className="font-medium">Agentul a decis singur tot planul de mâine.</p>
          <p className="mt-1 text-white/75">Nimic nu așteaptă un om.</p>
        </Panel>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[minmax(320px,400px)_minmax(0,1fr)]">
          <nav
            aria-label="Cazuri care așteaptă un om"
            data-lenis-prevent
            className="lg:sticky lg:top-28 lg:max-h-[calc(100svh-140px)] lg:self-start lg:overflow-y-auto lg:pr-1"
          >
            <ul className="space-y-2">
              {QUEUE.map((q) => (
                <li key={q.id}>
                  <QueueCard q={q} selected={q.id === selected.id} to={`/app/coada/${q.id}`} />
                </li>
              ))}
            </ul>
          </nav>
          <section aria-label={`Lucrarea ${item.label}`} className="min-w-0">
            <h2 className="mb-4 text-[clamp(1.3rem,1.8vw,1.7rem)] leading-tight font-semibold">{item.label}</h2>
            <ItemDetail item={item} />
          </section>
        </div>
      )}
    </>
  )
}

/* ---------------- Alerte ---------------- */

export function AlertsScreen() {
  return (
    <>
      <Title lead="Alertele pentru dispecerat și mesajele către echipe și clienți. Mesajele sunt doar previzualizări: demo, nu s-a trimis nimic.">
        Alerte și notificări
      </Title>
      <div className="grid gap-6 xl:grid-cols-12">
        <div className="space-y-3 xl:col-span-7">
          {DB.alerts.map((a) => (
            <Panel key={a.id}>
              <div className={cn("font-semibold", a.severity === "critical" ? "text-ember" : "text-white")}>{a.title}</div>
              <p className="mt-1 text-white/85">{a.body}</p>
            </Panel>
          ))}
        </div>
        <Panel title={`Notificări (${DB.summary.notifications})`} className="self-start xl:col-span-5">
          <ul className="space-y-4">
            {DB.notifications.map((n) => (
              <li key={n.id}>
                <div className="text-sm text-white/60">Către {n.audience}, demo, nu s-a trimis</div>
                <p className="mt-0.5 text-white/90">{n.message}</p>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </>
  )
}

/* ---------------- Jurnal ---------------- */

const ACTION_RO: Record<string, string> = {
  run: "Rulare",
  fusion: "Fuziune A cu bilanțul",
  remote_action: "Verificare de la distanță",
  assigned: "Echipă trimisă",
  deferred: "Amânat",
  human_review: "Trimis la om",
  notify: "Notificare",
}

export function JournalScreen() {
  const [filter, setFilter] = useState<string>("toate")
  const rows = filter === "toate" ? DB.audit : DB.audit.filter((a) => a.action === filter)
  const total = Object.values(DB.auditCounts).reduce((a, b) => a + b, 0)
  return (
    <>
      <Title lead={`Jurnalul are ${fmt(total)} de rânduri pentru planul acesta: fiecare decizie, cu predicția, modelul, regula și motivul. Mai jos, câte un eșantion din fiecare fel de decizie.`}>
        Jurnalul deciziilor
      </Title>
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <ThemedSelect
          label="Acțiunea"
          value={filter}
          onChange={setFilter}
          options={[
            { value: "toate", label: "Toate" },
            ...Object.keys(ACTION_RO).map((a) => ({ value: a, label: `${ACTION_RO[a]} (${fmt(DB.auditCounts[`agent:${a}`] ?? 0)})` })),
          ]}
        />
      </div>
      <Panel>
        {rows.length === 0 ? (
          <p>Nicio intrare de acest fel în eșantion.</p>
        ) : (
          <table data-ui className="w-full text-left">
            <thead>
              <tr className="text-sm text-white/60">
                <th className="pb-3 font-normal">Când</th>
                <th className="pb-3 font-normal">Acțiunea</th>
                <th className="pb-3 font-normal">Motivul</th>
                <th className="hidden pb-3 font-normal xl:table-cell">Urmărire</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.id} className="border-t border-white/10 align-top">
                  <td className="tabular py-3 pr-4 whitespace-nowrap text-white/70">{a.ts.slice(11)}</td>
                  <td className="py-3 pr-4">
                    <div className="font-medium whitespace-nowrap">{ACTION_RO[a.action] ?? a.action}</div>
                    {a.workItem &&
                      (ITEM_PAGE.has(a.workItem) ? (
                        <Link to={`/app/lucrari/${a.workItem}`} className="text-sm text-white/65 underline-offset-4 hover:underline">
                          {a.workItem}
                        </Link>
                      ) : (
                        <div className="text-sm text-white/55">{a.workItem}</div>
                      ))}
                  </td>
                  <td className="py-3 pr-4 text-white/85">
                    <span className="line-clamp-3">{a.note}</span>
                  </td>
                  <td className="hidden py-3 text-sm text-white/60 xl:table-cell">
                    {a.rule && <div>{a.rule}</div>}
                    {a.model && <div>{a.model}</div>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </>
  )
}

/* ---------------- Modele și evaluare ---------------- */

const METRIC_RO: Record<string, string> = {
  pr_auc: "PR AUC",
  roc_auc: "ROC AUC",
  precision_at_k: "precizie în primele K",
  recall_at_k: "recall în primele K",
  value_at_k_lei: "valoare în primele K (lei)",
  brier: "Brier (mai mic e mai bine)",
  recall_at_thr: "recall la prag",
  precision_at_thr: "precizie la prag",
  mae_vmax_pu: "eroare medie (pu, mai mic e mai bine)",
  coverage_p10_p90: "acoperirea intervalului P10–P90",
  pr_auc_exceed: "PR AUC depășire 1,10 pu",
  roc_auc_exceed: "ROC AUC depășire 1,10 pu",
  diagnoza_macro_f1: "F1 macro, diagnosticul cauzei",
  diagnoza_accuracy: "acuratețea diagnosticului",
  normal_mae_kwh_day: "eroarea pierderii normale (kWh/zi, mai mic e mai bine)",
  normal_coverage_p10_p90: "acoperirea intervalului P10–P90",
}
const SHOW: Record<string, string[]> = {
  A: ["roc_auc", "pr_auc", "precision_at_k", "value_at_k_lei"],
  B: ["roc_auc", "pr_auc", "recall_at_thr", "brier"],
  C: ["mae_vmax_pu", "roc_auc_exceed", "pr_auc_exceed", "coverage_p10_p90"],
  bilant: ["diagnoza_macro_f1", "diagnoza_accuracy", "normal_mae_kwh_day", "normal_coverage_p10_p90"],
}
const LOWER_IS_BETTER = new Set(["brier", "mae_vmax_pu", "normal_mae_kwh_day"])

function ModelPanel({ k, card }: { k: "A" | "B" | "C" | "bilant"; card: ModelCard }) {
  const name = k === "bilant" ? "Bilanț pe post" : SOURCES[k].name
  return (
    <Panel>
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <h2 className="font-sans text-lg font-semibold tracking-[-0.01em]">{name}</h2>
        <span className="text-sm text-white/55">{card.version}</span>
      </div>
      <p className="mt-1 text-white/80">{MODEL_LINES[k].what}</p>
      {k === "bilant" && <p className="mt-1 text-white/70">Rezultatele afișate sunt pentru modelul anterior; modelul FeederBW activ are evaluare separată, cu etichete sintetice.</p>}
      <table data-ui className="tabular mt-4 w-full text-left text-[15px]">
        <thead>
          <tr className="text-sm text-white/60">
            <th className="pb-2 font-normal">Metrica</th>
            <th className="pb-2 pl-4 text-right font-normal">Modelul</th>
            <th className="pb-2 pl-4 text-right font-normal">Reperul</th>
          </tr>
        </thead>
        <tbody>
          {SHOW[k].map((m) => {
            const v = card.metrics[m]
            const b = card.baseline?.[m]
            const better = b === undefined ? null : LOWER_IS_BETTER.has(m) ? v < b : v > b
            return (
              <tr key={m} className="border-t border-white/10">
                <td className="py-2 pr-4 text-white/85">{METRIC_RO[m] ?? m}</td>
                <td className={cn("py-2 pl-4 text-right font-semibold", better && "text-ok")}>{fmt(v, v > 100 ? 0 : 3)}</td>
                <td className="py-2 pl-4 text-right text-white/65">{b === undefined ? "fără" : fmt(b, b > 100 ? 0 : 3)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <details className="mt-4 text-sm text-white/70">
        <summary className="cursor-pointer text-white/85 hover:text-white">Date, reper și cum se reproduce</summary>
        <p className="mt-2">Reper: {card.baselineId}</p>
        <p className="mt-2">Împărțire: {card.split}</p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          {card.dataset.map((d) => (
            <li key={d}>{d}</li>
          ))}
        </ul>
        <p className="mt-2 break-all">Reproducere: {card.reproduce}</p>
      </details>
    </Panel>
  )
}

export function ModelsScreen() {
  const { gain, best } = agentGain()
  return (
    <>
      <Title lead="Fiecare model e comparat cu un reper simplu pe date de test separate (gospodării, perioade sau rețele nevăzute). Verde: modelul bate reperul.">
        Modele și evaluare
      </Title>
      <div className="grid gap-6 xl:grid-cols-2">
        {(["A", "B", "C", "bilant"] as const).map((k) => (
          <ModelPanel key={k} k={k} card={DB.modelCards[k]} />
        ))}
      </div>

      <h2 className="mt-12 mb-4 text-[clamp(1.2rem,1.6vw,1.5rem)] font-semibold">Agentul față de strategii simple</h2>
      <Panel>
        <p className="mb-5 max-w-[70ch] text-white/85">
          Pe {DB.evaluation.days} de zile sintetice, cu adevărul cunoscut, agentul aduce cu {gain}% mai multă valoare netă decât cea mai
          bună strategie simplă ({best.name.toLowerCase()}).
        </p>
        <EvalTable />
        <p className="mt-4 break-all text-sm text-white/55">Reproducere: {DB.evaluation.reproduce}</p>
      </Panel>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <Panel title="Robustețe: un model supra-încrezător">
          <p className="mb-4 text-white/80">
            {DB.evaluation.robust.days} zile în care scorurile modelelor sunt mai optimiste decât realitatea. Agentul rămâne primul.
          </p>
          <table data-ui className="tabular w-full text-left text-[15px]">
            <thead>
              <tr className="text-sm text-white/60">
                <th className="pb-2 font-normal">Strategie</th>
                <th className="pb-2 text-right font-normal">Valoare netă pe zi</th>
                <th className="pb-2 text-right font-normal">Urgențe ratate</th>
              </tr>
            </thead>
            <tbody>
              {DB.evaluation.robust.rows.map((r) => (
                <tr key={r.key} className="border-t border-white/10">
                  <td className={cn("py-2 pr-4", r.key === "agent" ? "font-semibold" : "text-white/85")}>{r.name}</td>
                  <td className="py-2 text-right">{fmt(r.netLeiDay)} lei</td>
                  <td className="py-2 text-right">{fmt(r.urgentMissedRate * 100, 1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
        <Panel title="Ce se schimbă dacă scoatem o piesă">
          <ul className="space-y-4">
            {DB.evaluation.ablations.map((a) => (
              <li key={a.key}>
                <div className="font-medium">{a.label}</div>
                <div className="tabular text-white/75">
                  {fmt(a.netLeiDay)} lei pe zi, {fmt(a.uselessRate * 100, 1)}% vizite degeaba, {fmt(a.urgentMissedRate * 100, 1)}% urgențe ratate
                </div>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-sm text-white/60">
            Fără pragul etic agentul ar câștiga mai mult, dar ar trimite echipe la oameni pe un scor sub 0,5. Pragul rămâne.
          </p>
        </Panel>
      </div>
    </>
  )
}

/* ---------------- Contul meu ---------------- */

export function AccountScreen() {
  const { user, profile, loading, saveProfile, signOut } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState("")
  const [team, setTeam] = useState<Team | "">("")
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<{ tone: "ok" | "err"; text: string } | null>(null)
  const nameId = useId()
  const teamId = useId()

  useEffect(() => {
    setName(profile?.full_name ?? "")
    setTeam(profile?.team ?? "")
  }, [profile])

  if (loading) {
    return (
      <>
        <Title>Contul meu</Title>
        <div className="h-64 animate-pulse rounded-2xl bg-surface" aria-label="Se încarcă" />
      </>
    )
  }

  if (!user) {
    return (
      <>
        <Title lead="Cu un cont, deciziile și echipa ta rămân salvate pe orice calculator.">Contul meu</Title>
        <Panel>
          <p className="font-medium">Nu ești conectat.</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <GlassLink
              href={ROUTES.signIn}
              variant="blue"
              onClick={(e) => {
                e.preventDefault()
                navigate(ROUTES.signIn)
              }}
            >
              Intră în cont
            </GlassLink>
            <GlassLink
              href={`${ROUTES.signIn}?mod=cont-nou`}
              variant="frost"
              onClick={(e) => {
                e.preventDefault()
                navigate(`${ROUTES.signIn}?mod=cont-nou`)
              }}
            >
              Creează un cont
            </GlassLink>
          </div>
        </Panel>
      </>
    )
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) {
      setMsg({ tone: "err", text: "Scrie-ți numele, ca să știe echipa cine a aprobat." })
      return
    }
    setBusy(true)
    setMsg(null)
    const err = await saveProfile({ full_name: name.trim(), team: team || null })
    setBusy(false)
    setMsg(err ? { tone: "err", text: err } : { tone: "ok", text: "Profilul a fost salvat." })
  }

  const dirty = name !== (profile?.full_name ?? "") || team !== (profile?.team ?? "")

  return (
    <>
      <Title lead={user.email}>{displayName(user, profile)}</Title>
      <div className="grid gap-6 xl:grid-cols-12">
        <Panel title="Profil" className="xl:col-span-7">
          <form onSubmit={submit} noValidate className="space-y-5">
            <div>
              <label htmlFor={nameId} className="mb-2 block font-medium">
                Nume
              </label>
              <input
                id={nameId}
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
                disabled={busy}
                className="h-12 w-full rounded-2xl bg-surface-2 px-4 outline-none focus-visible:ring-2 focus-visible:ring-ember disabled:opacity-60"
              />
            </div>
            <div>
              <div id={teamId} className="mb-2 font-medium">
                Echipa
              </div>
              <ThemedSelect<Team | "">
                value={team}
                onChange={setTeam}
                disabled={busy}
                options={[{ value: "", label: "Nicio echipă" }, ...TEAMS.map((t) => ({ value: t, label: t }))]}
              />
            </div>
            {msg && (
              <p role={msg.tone === "err" ? "alert" : "status"} className={msg.tone === "err" ? "text-bad" : "text-ok"}>
                {msg.text}
              </p>
            )}
            <GlassButton type="submit" disabled={busy || !dirty}>
              {busy && <Loader2 className="size-4 animate-spin" aria-hidden />}
              {busy ? "Se salvează…" : "Salvează profilul"}
            </GlassButton>
          </form>
        </Panel>
        <Panel title="Sesiune" className="xl:col-span-5">
          <p className="text-white/85">Ieși din cont pe acest calculator. Deciziile rămân salvate în cont.</p>
          <button
            type="button"
            onClick={async () => {
              await signOut()
              navigate(ROUTES.home)
            }}
            className="mt-5 inline-flex h-11 cursor-pointer items-center gap-2 rounded-full bg-white/[0.08] px-5 font-medium transition-colors duration-150 hover:bg-white/15"
          >
            <LogOut className="size-4" aria-hidden />
            Ieși din cont
          </button>
        </Panel>
      </div>
    </>
  )
}
