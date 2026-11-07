# Status: Teo-landing
Actualizat: 2026-11-07 17:20
Milestone curent: M0 (19:00: research pe cele 10 site-uri, direcția vizuală, structura secțiunilor, hero-ul randat)
Gata de merge: nu

## Făcut
- 17:16 Citite: `prompts/_comun.md`, `AGENTS.md`, `memory/INDEX.md`, jurnalul, `07-tema-ppc.md`, `10-implementare.md`, `11-bilant-pe-post.md`, `12-probleme-reale-ppc-2026.md`, `status/Teo-ui.md`, `status/Teo-prezentare.md`, `reports/*/metrics.json`, `reports/planner/agent_eval.md`.

## Urmează
- Capturi și structura celor 10 site-uri de referință, plus site-urile PPC (ppcgroup.com, ppcenergy.ro) → `docs/research/landing.md` (ce iau din fiecare, de ce, licențele componentelor).
- Schelet `landing/` (Next.js + Tailwind 4 + bun, export static), fontul ales cu ș/ț verificate, paleta PPC cu contrast AA.
- Hero-ul randat, capturi la 1920×1080, 1440 și mobil, pentru Teo înainte de restul secțiunilor.

## Blocaje
- niciunul

## Cereri către orchestrator
- (17:20) Răspuns la întrebarea despre limbă: landing-ul e **în română** (textul, explicațiile, cifrele, cu ș/ț corecte), cu **titluri scurte în engleză** (cel mult 5 cuvinte), aceleași ca în film acolo unde se potrivesc. Ca în film: titlul în engleză, iar sub el fraza în română.

## Cum se rulează (comenzile exacte)
- În lucru. Portul landing-ului: **3730** (`cd landing && bun dev`). 3720 rămâne al previzualizării video.

## Cifre (doar din scripturi, cu comanda)
- niciuna încă. Cifrele modelelor se citesc la build din `reports/<A|B|C|bilant>/metrics.json` și `reports/planner/agent_eval.json`; unde lipsesc, cadrul rămâne „în lucru”. La A nu se afișează precizia@K de 1,00 (Londra, defecte evidente), doar problemele subtile și SGCC.

## Decizii (cu ora)
- 17:18 Port 3730 (cererea orchestratorului; 3720 e al previzualizării video).
- 17:18 Limba: româna pentru tot textul, titluri scurte în engleză (cel mult 5 cuvinte), ca în film.
- 17:19 Capturile site-urilor de referință: `agent-browser` în mod headless, doar vizualizare, fără conturi și formulare. Jev nu salvează capturi (raportează doar done/blocked și URL-ul), iar studiul cere capturi la rezoluții fixe pe fiecare secțiune; așa nu se deschid nici tab-uri în Helium-ul lui Teo.
- 17:19 Nimic peste 5 MB în git: `landing/node_modules`, `landing/.next`, `landing/out` ignorate; imagini în WebP/AVIF, fonturi woff2, filmul legat, nu pus în repo.
