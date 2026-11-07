# Status: Teo-landing
Actualizat: 2026-11-07 17:45
Milestone curent: M0 (19:00) gata devreme: research, direcția, structura, hero-ul randat. Aștept părerea lui Teo pe capturi înainte de restul secțiunilor.
Gata de merge: nu (după ce Teo vede hero-ul)

## Făcut
- 17:16 Citite: `prompts/_comun.md`, `AGENTS.md`, memoria (INDEX, jurnal, 07, 10, 11, 12), `status/Teo-ui.md`, `status/Teo-prezentare.md`, `reports/*/metrics.json`, `reports/planner/agent_eval.md`, cadrele filmului (`presentation/frames-codex/v1/FRAMES.md`, textele în engleză).
- 17:25 Research pe cele 10 site-uri plus ppcenergy.ro (capturi headless la 1440×900 și 390×844, fonturi, culori, biblioteci): `docs/research/landing.md` (ce iau din fiecare și de ce, licențele, fontul, paleta). ppcgroup.com și reteleelectrice.ro blochează browserele automate; paleta lor vine din verificarea firului Interfață.
- 17:28 Font: **Figtree** (OFL), cel mai apropiat liber de PingLCG din 12 comparate; ș/ț/Ș/Ț cu virgulă verificate în fișierele woff2, cifre tabulare.
- 17:30 Paleta PPC cu contrast AA pe `#000f1e` (text 17,3; albastru PPC 6,7; portocaliu 5,5; buton alb pe `#163fe8` 7,2). Culorile surselor A/B/C din consolă (varianta închisă).
- 17:40 Aplicația `landing/` (Next.js 16.4, Tailwind 4, bun, export static) și hero-ul: harta României din puncte, zona Rețele Electrice aprinsă, lucrările reale din planul demo (8 iulie 2025, din `outputs/demo/`), traseele celor 8 echipe, lupa peste București și Ilfov, cercuri portocalii la cele 25 de cazuri pentru om; secvența Perceive → Estimate → Decide → Act doar în CSS, oprită de `prefers-reduced-motion`; arcul de orizont în culorile PPC.
- 17:48 Hero reordonat: pe mobil harta vine imediat după butoane (pașii după hartă). `make check` trece (277 de teste).
- 17:42 Exportul static (`bun run build`, 4 s) merge și deschis direct de pe disc (file://): fontul se încarcă, fără erori. `tsc` și `eslint` trec.
- Capturi pentru Teo: `landing/design/captures/hero-1920x1080.webp`, `hero-1440x900.webp`, `hero-390x844.webp`, `hero-1440-secventa-2-7s.webp` (mijlocul animației).

## Urmează
- După părerea lui Teo pe hero: secțiunile Problema, Agentul, Sursele, Scara C, Omul în buclă, Explicabilitate, Rezultate, Demo, Echipa (structura în `docs/research/landing.md`).
- Cifrele modelelor citite la build din `reports/`; „în lucru” unde lipsesc.

## Blocaje
- niciunul

## Cereri către orchestrator
- (17:20) Limba: landing-ul e **în română** (textul, explicațiile, cifrele, cu ș/ț corecte), cu **titluri scurte în engleză** (cel mult 5 cuvinte), aceleași ca în film acolo unde se potrivesc (ex. „Tomorrow’s crews, planned tonight.”, „Not sure? It asks you.”).
- (17:45) Nimic de îmbinat încă; scriu „Gata de merge: da” după ce Teo vede hero-ul.
- (17:50) JURNAL, pentru `memory/journal.md` (eu nu scriu în `memory/`): „17:45 Landing (fir nou Teo-landing, pornit la 17:15 de Teo): direcția vizuală = culorile PPC ca răsărit, hero cu harta României din puncte și planul real al zilei demo; font Figtree (liber, apropiat de PingLCG); port 3730; text în română, titluri scurte în engleză ca în film. Research în docs/research/landing.md.”

## Cum se rulează (comenzile exacte)
- Dezvoltare: `cd landing && bun install && bun dev` → http://localhost:3730
- Export static: `cd landing && bun run build` → `landing/out/` (se deschide și direct: `open landing/out/index.html`)
- Verificarea exportului pe server: `cd landing && bun run preview` → http://localhost:3730
- `cd landing && bun run lint && bun run typecheck`
- Portul: **3730** (3720 e al previzualizării video).

## Cifre (doar din scripturi, cu comanda)
- Hero-ul arată numerele planului demo citite la build din `outputs/demo/plans/demo-vara/plan.json` și `work_items.jsonl` (instantaneul planificatorului, `uv run python -m cyberpunks.planner.snapshot --scenario demo-vara`): 697 de lucrări (A 630, B 26, C 41), 20 în traseele a 8 echipe, 504 verificate de la distanță, 25 la un om.
- Cifrele modelelor vin doar din `reports/<A|B|C|bilant>/metrics.json` și `reports/planner/agent_eval.json`. La A nu afișez precizia@K de 1,00; afișez problemele subtile și SGCC, cu valorile din fișier (acum 0,625 față de 0,016 și 0,80 față de 0,106; orchestratorul a scris 0,61/0,02 și 0,81/0,11, cifrele mai vechi).

## Decizii (cu ora)
- 17:18 Port 3730 (cererea orchestratorului).
- 17:18 Limba: româna pentru tot textul, titluri scurte în engleză (cel mult 5 cuvinte), ca în film.
- 17:19 Capturile site-urilor de referință: `agent-browser` headless, doar vizualizare. Jev nu salvează capturi (raportează doar done/blocked și URL-ul), iar studiul cere capturi la rezoluții fixe; așa nu se deschid nici tab-uri în Helium-ul lui Teo.
- 17:19 Nimic peste 5 MB în git: `landing/node_modules`, `.next`, `out` ignorate; capturile în WebP (27-135 KB); filmul se leagă, nu intră în repo.
- 17:28 Figtree în locul lui Archivo (fontul consolei): brief-ul cere un font apropiat de PingLCG; culorile surselor rămân cele din consolă, ca să fie același produs.
- 17:30 Direcția: culorile PPC ca răsărit (bleumarin → albastru → cian → soarele portocaliu); portocaliul înseamnă, ca în consolă, „decide un om”; traseele agentului în alb, ca în film.
- 17:35 Hero-ul folosește planul real din `outputs/demo/` (nu date desenate de mână), etichetat: activele, echipele și bazele sunt sintetice, pe hartă reală; vremea e reală.
- 17:40 Animația hero-ului doar în CSS, fără JS: merge și de pe disc; cu reduced motion se vede direct starea finală.
- 17:41 `experimental.inlineCss` și scriptul `landing/scripts/relativize.ts` fac căile relative după build, ca pagina să meargă de pe disc în sală.
- 17:43 Nicio componentă copiată încă (hero-ul e scris de noi). Dacă preiau cod: React Bits e MIT + Commons Clause (permis într-un site), shadcn, beUI gratuit și Amicro sunt MIT; Originkit, bencho, beautifului, sceneai doar ca inspirație.
