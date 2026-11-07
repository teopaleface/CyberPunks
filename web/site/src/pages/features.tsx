import { useEffect, useState } from "react"
import { BalanceExplorer, DiagnosisBars } from "@/components/balance-explorer"
import { Block, NextStep, PageShell } from "@/components/page"
import { ApprovedCounter, QueueTable } from "@/components/ranking-board"
import { Reveal } from "@/components/reveal"
import { useLenis } from "@/components/smooth-scroll"
import { DB, DIAGNOSIS_RO, PLAN_DATE_RO, SYNTHETIC_NOTE } from "@/data/daybreak"
import { TO_CONFIRM, EvalTable, agentGain } from "@/sections/demo"
import { ActVisual, DecideVisual, EstimateVisual, PerceiveVisual, STEPS } from "@/sections/how-it-works"
import { PlanFigures } from "@/sections/plan"
import { cn, fmt } from "@/lib/utils"

/* ======================= Planul de mâine ======================= */

export function PlanPage() {
  return (
    <PageShell
      title="Planul de mâine"
      lead={`Ce face agentul într-o noapte: din ${fmt(DB.summary.items_in)} de lucrări posibile, alege ce merge la echipe, ce se verifică de la distanță și ce decide un om. Planul real pentru ${PLAN_DATE_RO}.`}
    >
      <Block title="Cifrele zilei" intro={SYNTHETIC_NOTE}>
        <div data-ui className="rounded-2xl bg-surface p-[clamp(24px,3vw,44px)]">
          <PlanFigures />
        </div>
      </Block>
      <Block title="Ce a decis agentul" intro="Fiecare lucrare primește o singură decizie, cu regula care a produs-o.">
        <div data-ui className="rounded-2xl bg-surface p-[clamp(20px,3vw,40px)]">
          <DecideVisual />
        </div>
      </Block>
      <Block title="Echipele" intro="Opt echipe, în limita turei și a abilităților lor. Traseele sunt calculate cu OR-Tools.">
        <div data-ui className="rounded-2xl bg-surface p-[clamp(20px,3vw,40px)]">
          <ActVisual />
        </div>
      </Block>
      <Block title="Ce rămâne la un om" intro="Cazurile în care agentul nu e sigur. Aprobă-le aici; cu un cont, deciziile se păstrează.">
        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-8">
            <QueueTable limit={5} />
          </div>
          <div className="lg:col-span-4">
            <ApprovedCounter />
          </div>
        </div>
      </Block>
      <NextStep text="Harta, lucrările, alertele și jurnalul sunt în aplicație." label="Deschide aplicația" to="/app" />
    </PageShell>
  )
}

/* ======================= Bilanț ======================= */

const INPUTS = [
  { t: "Contorul de bilanț al postului", d: "Energia ieșită din post, la fiecare 15 minute." },
  { t: "Contoarele clienților", d: "Consumul și producția fiecăruia la 15 minute, opțional și tensiunea." },
  { t: "Lista client → post", d: "Ce casă la ce post este legată." },
  { t: "Vremea", d: "Temperatura și soarele, ca să explice consumul normal." },
  { t: "Prețul energiei", d: "Ca să transformăm kWh în lei." },
]

export function BilantPage() {
  const m = DB.modelCards.bilant
  return (
    <PageShell
      title="Bilanțul pe fiecare post"
      lead="Energia ieșită din post minus suma contoarelor clienților. Modelul învață pierderea normală a fiecărui post și ghicește cauza a ce lipsește peste ea; agentul decide ce facem."
    >
      <Block title="Alege un post" intro="Opt posturi din planul real, câte unul pentru fiecare cauză, plus cele mai mari pierderi.">
        <BalanceExplorer full />
      </Block>

      <Block title="Mai bun decât regulile de azi" intro="Pe date de test separate, față de reperul din concept (formula fizică pentru normal, tabelul de reguli pentru cauză).">
        <dl className="tabular grid gap-6 md:grid-cols-3">
          <div data-ui className="rounded-2xl bg-surface p-6">
            <dd className="text-4xl font-semibold">
              {fmt(m.metrics.normal_mae_kwh_day, 1)} <span className="text-lg text-white/70">kWh/zi</span>
            </dd>
            <dt className="mt-2 text-white/80">eroarea pierderii normale, față de {fmt(m.baseline.normal_mae_kwh_day, 1)} la formula fizică</dt>
          </div>
          <div data-ui className="rounded-2xl bg-surface p-6">
            <dd className="text-4xl font-semibold">{fmt(m.metrics.diagnoza_macro_f1, 2)}</dd>
            <dt className="mt-2 text-white/80">F1 la ghicirea cauzei, față de {fmt(m.baseline.diagnoza_macro_f1, 2)} la tabelul de reguli</dt>
          </div>
          <div data-ui className="rounded-2xl bg-surface p-6">
            <dd className="text-4xl font-semibold">{fmt(m.metrics.diagnoza_abstain_rate * 100)}%</dd>
            <dt className="mt-2 text-white/80">din posturi primesc „nu sunt sigur” în loc de o cauză ghicită</dt>
          </div>
        </dl>
      </Block>

      <Block title="Din ce se calculează">
        <dl className="grid gap-x-12 gap-y-8 md:grid-cols-2 lg:grid-cols-3">
          {INPUTS.map((x) => (
            <div key={x.t}>
              <dt className="font-semibold">{x.t}</dt>
              <dd className="mt-1 text-white/80">{x.d}</dd>
            </div>
          ))}
        </dl>
      </Block>

      <Block title="De confirmat cu PPC">
        <ul className="max-w-[70ch] space-y-4">
          {TO_CONFIRM.map((c) => (
            <li key={c} className="flex gap-3">
              <span aria-hidden className="mt-2.5 size-2 shrink-0 rounded-full bg-ember" />
              <span className="text-white/90">{c}</span>
            </li>
          ))}
        </ul>
      </Block>

      <NextStep text="Pagina fiecărui post, cu urmărirea până la model, e în aplicație." label="Vezi posturile" to="/app/posturi" />
    </PageShell>
  )
}

/* ======================= Diagnostic ======================= */

const DIAGNOSES = [
  { key: "contor_client", sees: "Un contor e blocat, are ceasul decalat sau dă valori negative", team: "Echipa de contoare, după o citire de la distanță" },
  { key: "furt_inainte_contor", sees: "Lipsa a apărut brusc într-o zi și e constantă, iar toate contoarele par normale", team: "Echipa de control" },
  { key: "pierdere_tehnica", sees: "Lipsa crește mult când postul e încărcat, iar fazele sunt dezechilibrate", team: "Echipa de rețea" },
  { key: "client_post_gresit", sees: "Un contor „seamănă” cu clienții altui post", team: "Corecție în birou, fără deplasare" },
  { key: "contor_bilant_setat", sees: "Contorul de bilanț arată exact de 2× mai mult decât ar trebui", team: "Echipa de contoare" },
]

export function DiagnosticPage() {
  const lenis = useLenis()
  const [active, setActive] = useState(0)
  const f1 = DB.modelCards.bilant.metrics

  useEffect(() => {
    const els = DIAGNOSES.map((_, i) => document.getElementById(`cauza-${i}`)).filter(Boolean) as HTMLElement[]
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(Number(e.target.id.split("-")[1]))),
      { rootMargin: "-45% 0px -50% 0px" }
    )
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])

  const jump = (i: number) => {
    const el = document.getElementById(`cauza-${i}`)
    if (!el) return
    if (lenis) lenis.scrollTo(el, { offset: -120 })
    else el.scrollIntoView({ behavior: "smooth" })
  }

  return (
    <PageShell
      title="De ce lipsește energia"
      lead="Forma lipsei spune cauza. Pentru fiecare cauză, agentul știe cine trebuie să meargă, sau dacă e de ajuns o corecție din birou."
    >
      <div className="container-page mt-[clamp(64px,10vh,120px)] grid gap-12 lg:grid-cols-12">
        <aside className="hidden lg:col-span-3 lg:block">
          <nav aria-label="Cauze" className="sticky top-32">
            <ul className="space-y-1">
              {DIAGNOSES.map((d, i) => (
                <li key={d.key}>
                  <button
                    type="button"
                    onClick={() => jump(i)}
                    aria-current={active === i ? "true" : undefined}
                    className={cn(
                      "relative w-full cursor-pointer rounded-2xl py-2.5 pr-3 pl-5 text-left transition-colors duration-150",
                      active === i ? "bg-surface text-white" : "text-white/70 hover:text-white"
                    )}
                  >
                    {active === i && <span aria-hidden className="absolute inset-y-3 left-0 w-1 rounded-full bg-ember" />}
                    {DIAGNOSIS_RO[d.key]}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </aside>
        <div className="space-y-[clamp(64px,10vh,120px)] lg:col-span-9">
          {DIAGNOSES.map((d, i) => {
            const example = DB.cases.find((c) => c.diagnosis === d.key)
            const n = DB.posts.filter((p) => p.diagnosis === d.key).length
            return (
              <section key={d.key} id={`cauza-${i}`} className="scroll-mt-32">
                <Reveal>
                  <h2 className="text-[clamp(1.6rem,2.6vw,2.4rem)] leading-tight font-semibold">{DIAGNOSIS_RO[d.key]}</h2>
                </Reveal>
                <Reveal delay={0.06} data-ui className="mt-6 grid gap-8 rounded-2xl bg-surface p-[clamp(20px,3vw,36px)] md:grid-cols-2">
                  <dl className="space-y-5">
                    <div>
                      <dt className="text-sm text-white/60">Ce vede aplicația</dt>
                      <dd className="mt-1">{d.sees}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-white/60">Cine merge</dt>
                      <dd className="mt-1 font-medium">{d.team}</dd>
                    </div>
                    <div className="tabular flex gap-10">
                      <div>
                        <dd className="text-2xl font-semibold">{n}</dd>
                        <dt className="text-sm text-white/60">posturi în plan</dt>
                      </div>
                      <div>
                        <dd className="text-2xl font-semibold">{fmt(f1[`diagnoza_f1_${d.key}`] ?? 0, 2)}</dd>
                        <dt className="text-sm text-white/60">F1 pe test</dt>
                      </div>
                    </div>
                  </dl>
                  {example ? (
                    <figure>
                      <figcaption className="mb-3 text-sm text-white/70">{example.label}: ce vede modelul</figcaption>
                      <DiagnosisBars c={example} />
                    </figure>
                  ) : (
                    <p className="text-white/70">Niciun post din plan nu are această cauză azi.</p>
                  )}
                </Reveal>
              </section>
            )
          })}
        </div>
      </div>

      <Block title="Mai mult decât contoare ciudate" intro="PPC are deja detecție de fraudă pe contoare. Bilanțul pe post adaugă ce contoarele singure nu văd.">
        <ul className="grid gap-x-12 gap-y-6 md:grid-cols-2">
          {[
            ["Confirmare independentă", "Un contor suspect pe un post unde chiar lipsește energie este o pistă aproape sigură. Mai puține deplasări degeaba."],
            ["Problema în lei", "Echipele merg întâi unde se pierd cei mai mulți bani."],
            ["Ce nu se vede din contor", "Furt înainte de contor, cabluri care pierd mult, faze dezechilibrate."],
            ["Un cost real", "Distribuitorul plătește energia pierdută peste cât îi recunoaște ANRE."],
          ].map(([t, d]) => (
            <li key={t}>
              <h3 className="font-sans font-semibold">{t}</h3>
              <p className="mt-1 text-white/80">{d}</p>
            </li>
          ))}
        </ul>
      </Block>

      <NextStep text="Vezi fiecare post și decizia agentului pentru el." label="Deschide bilanțul" to="/app/posturi" />
    </PageShell>
  )
}

/* ======================= Agent ======================= */

const VISUALS = [<PerceiveVisual key="p" />, <EstimateVisual key="e" />, <DecideVisual key="d" />, <ActVisual key="a" />]

export function AgentPage() {
  const { gain } = agentGain()
  return (
    <PageShell
      title="Agentul care pregătește ziua"
      lead="Percepe, estimează, decide, acționează. Reguli scrise în cod, nu un LLM, iar nicio echipă nu pleacă la un om pe un scor nesigur."
    >
      {STEPS.map((s, i) => (
        <Block key={s.title} title={s.title} intro={s.body}>
          <div data-ui className="rounded-2xl bg-surface p-[clamp(20px,3vw,40px)]">
            {VISUALS[i]}
          </div>
        </Block>
      ))}

      <Block title={`Cu ${gain}% mai multă valoare decât strategiile simple`} intro="Aceleași zile, aceleași echipe; doar felul de a decide diferă. Lume sintetică, cu adevărul cunoscut.">
        <div className="rounded-2xl bg-surface p-[clamp(20px,3vw,36px)]">
          <EvalTable />
        </div>
      </Block>

      <Block title="Reguli pe care nu le încalcă">
        <ul className="grid gap-x-12 gap-y-6 md:grid-cols-2">
          {[
            ["Întâi verificări ieftine", "Recitirea contorului și jurnalul de evenimente, de la distanță, înainte de orice deplasare."],
            ["În limita capacității", "Fiecare echipă primește doar cât poate face, ordonat după valoare, cu abilitățile și tura ei."],
            ["Un om decide ce nu e sigur", "Scor sub prag, zonă necunoscută modelului sau regiune plină: cazul merge la dispecer, cu motivul."],
            ["Totul în jurnal", "Fiecare decizie duce la predicția care a produs-o, la versiunea modelului și la regulă."],
          ].map(([t, d]) => (
            <li key={t}>
              <h3 className="font-sans font-semibold">{t}</h3>
              <p className="mt-1 text-white/80">{d}</p>
            </li>
          ))}
        </ul>
      </Block>

      <NextStep text="Jurnalul complet și coada pentru om sunt în aplicație." label="Deschide jurnalul" to="/app/jurnal" />
    </PageShell>
  )
}
