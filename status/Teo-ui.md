# Status: Teo-ui
Actualizat: 2026-11-07 12:48
Milestone curent: M0
Gata de merge: nu

## Făcut
- 12:45 Citite: prompts/_comun.md, prompts/ui.md, memory/ (INDEX, 07, 08, 10, journal), docs/PLAN.md, docs/CONTRACTS.md, contracts.py, contracts/fixtures/.
- 12:45 `uv sync` și `make check` trec (ruff curat, 7 teste).

## Urmează
- Faza 0 (până la ~13:35): paleta (trimitere discretă la PPC), font cu ș/ț verificat, hărți OpenFreeMap fără cheie, logo cu Codex, 3 direcții vizuale pe date reale arătate lui Teo.
- În paralel: scheletul Next.js în `web/` (bun, TypeScript, Tailwind, shadcn/ui, MapLibre, Recharts), port 3710, `make web`.
- M0 la 14:30: direcția aleasă, logo, proiectul Next.js pornit.

## Blocaje
- niciunul

## Cereri către orchestrator
- (în curând) fixture-uri de serii (`Series`) pentru câte o lucrare A, B, C, ca detaliul lucrării să aibă grafic înainte de API.

## Cum se rulează (comenzile exacte)
- (după schelet) `make web` → http://localhost:3710

## Cifre (doar din scripturi, cu comanda)
- niciuna încă (interfața doar afișează cifrele firelor)

## Decizii (cu ora)
- 12:48 Pornesc faza 0 cu subagenți în paralel: scheletul Next.js separat de direcția vizuală, ca M0 să prindă ora 14:30.
