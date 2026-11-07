# Convențiile consolei „Tura de mâine” (pentru oricine scrie ecrane noi)

Direcția vizuală: „Panou” (vezi `web/design/directions/panou.jpg`): disciplina panourilor de dispecerat. Totul e gri în repaus; culoarea apare doar când înseamnă ceva: sursa unei lucrări (A albastru, B mov-prună, C chihlimbar) sau ceva ce cere un om (portocaliu `att`). Proiector 1920×1080, temă deschisă.

## Stack și reguli Next 16

- Next.js 16.4 (App Router, **Cache Components activ**), React 19.3, Tailwind 4, shadcn/ui (`components/ui/*`), Recharts 3, bun. Port 3710.
- O pagină care citește date: componenta de pagină randează un `<Suspense fallback={…}>` cu un copil async care face `await connection()` (din `next/server`), apoi `const scenario = await resolveScenario(searchParams)` și `const { info } = await loadShellInfo(scenario)` (din `@/lib/server/queries`), apoi îmbracă totul în `<AppShell info={info}>` (din `@/components/shell/app-shell`). Model: `app/lucrari/[id]/page.tsx`, `app/page.tsx`.
- `export const dynamic` nu e permis. Fără `fetch` din client către API: datele vin prin stratul de date de pe server (`@/lib/data`: `getPlanView`, `getWorkItems`, `getAudit`, `getMetrics`, `getWorkItem`, `getSeries`, `getScenarios`), iar acțiunile prin acțiunile de server (`@/lib/data/actions`: `runAgent`, `submitReview`). Fiecare citire întoarce `{ data, source, degradedReason }`: când `degradedReason` există, arată-l discret.
- Componente client doar unde e nevoie de interacțiune. `cn` vine din pachetul `cn`.

## Tokenuri (Tailwind, din `app/globals.css`)

- Culori: `bg-canvas` (fundalul paginii), `bg-panel` (panouri, antet), `text-ink` (text), `text-muted-foreground`, `border-rule` (linii), `bg-muted` (umplere bare), `text-att` / `bg-att` / `text-att-ink` / `bg-att-surface` (doar pentru „decide un om” și avertismente), `bg-src-a` / `bg-src-b` / `bg-src-c` (sursele), `text-src-c-ink` (chihlimbar lizibil ca text), `bg-ok` (verde, doar pentru „în direct”).
- Fără umbre și fără carduri rotunjite identice: suprafețele se despart prin linii de 1 px (`border-rule`) și spațiu. Colțuri de 4 px (`rounded-[4px]`) doar pe controale.
- Tipografie: Archivo (variabil pe lățime). Utilitare: `num-wide` (cifre mari de panou), `num-tall` (ore înguste), `dense` și `code-id` (ID-uri, coduri de reguli). Text de bază 15–16 px, etichete minim 13 px. Cifrele sunt tabulare peste tot.
- Butoane: `<Button size="panel">` (40 px, 15 px), `variant="outline"` pentru secundare.

## Helpers existente (folosește-le, nu le dubla)

- `@/lib/format`: `fmtInt`, `fmtDec`, `fmtScore` (0,87), `fmtLei` (2.741 lei), `fmtKm`, `fmtTime` (08:25), `fmtDateLong` („Luni, 9 noiembrie 2026”), `fmtMoment`, `fmtDuration`, `fmtSeconds`, `sentence`, `plural`.
- `@/lib/data/labels`: `DECISION_LABEL_RO`, `CONFIDENCE_RO`, `ACTION_RO`, `SKILL_RO`, `predictionLabelRo`, `outcomeRo`, `ruleRo`, `thresholdLabelRo`, `thresholdValueRo`, `SOURCE_LABEL_RO`.
- `@/lib/sources`: `SOURCES` (numele și culoarea fiecărei surse). `@/lib/marker-svg`: `markerSvg({source, kind, selected})` (markerul cu litera sursei, ca șir SVG; în React: `<span className="block size-9" dangerouslySetInnerHTML={{__html: markerSvg(...)}} />`), `markerKind(decision)`.
- `@/lib/plan-screen`: `itemTitle(w)`, `itemPlace(w)`.
- `@/components/plan/score-scale`: `ScoreScale` (scor, interval, prag). `@/components/shell/provenance`: `SyntheticGlyph` (pătratul hașurat = date sintetice).
- `@/components/detail/review-actions`: `ReviewActions` (Aprobă / Respinge / Amână cu notă, legat la API).

## Scriere

- Română cu diacritice corecte (ș, ț cu virgulă). Cuvinte simple, din perspectiva dispecerului. Numere în format românesc.
- Butoanele spun exact ce fac. Erorile spun ce s-a întâmplat și ce poți face, fără scuze. Ecranele goale invită la o acțiune.
- Etichete de transparență vizibile: „Date sintetice” (cu `SyntheticGlyph`), „Model validat pe date externe”, iar pentru bilanț: „Simulare pe date publice, gândită pentru datele PPC”. Mesajele către clienți: „demo, nu s-a trimis”.
- De evitat (semne de design generat): etichete cu majuscule, eticheta mică deasupra fiecărui titlu, șiruri cu puncte la mijloc („A · B”), „→” lipit de butoane, carduri identice cu umbră, degradeuri decorative, numerotare decorativă.

## Grafice (abilitatea `dataviz`)

- O singură axă Y pe grafic; două mărimi diferite = două grafice. Legendă pentru ≥ 2 serii; textul în culorile de text, culoarea seriei doar pe semne. Tooltip la trecerea cu mouse-ul. Culorile categoriilor: A `var(--src-a)`, B `var(--src-b)`, C `var(--src-c)`; model față de baseline: modelul în `var(--ink)`, baseline-ul în `var(--idle)`.

## Verificare înainte de „gata”

- `cd web && bunx tsc --noEmit -p . && bun run lint && bun test` trec.
- Captură la 1920×1080 cu agent-browser (sesiune proprie: `export AGENT_BROWSER_SESSION="$(agent-browser session id --scope worktree --prefix <nume>)"`), serverul rulează deja pe http://localhost:3710 (nu porni altul). Te uiți la captură și repari: text tăiat, suprapuneri, diacritice, contrast.
- Nu face commit, push sau stash; scrie doar în fișierele tale.
