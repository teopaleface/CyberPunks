# CyberPunks: Daybreak

Proiectul echipei CyberPunks la SmartHack XI 2026 (7-8 noiembrie, București), pe tema PPC "24h to Power PPC": un agent AI care decide unde merg mâine echipele de teren Rețele Electrice, pe baza a trei modele ML antrenate de echipă (contoare defecte sau manipulate, risc de avarii la furtună, tensiune prea mare din cauza prosumatorilor), și explică fiecare decizie.

Stare: în lucru, vezi [`status/ACUM.md`](status/ACUM.md). Planul: [`docs/PLAN.md`](docs/PLAN.md). Formatele de date: [`docs/CONTRACTS.md`](docs/CONTRACTS.md). Contextul și research-ul: [`memory/`](memory/INDEX.md).

## Cum testezi

Ghidul pentru echipă, cu pornirea demo-ului într-o singură comandă (`make demo`) și ce verifici pe fiecare ecran: [`docs/TESTARE.md`](docs/TESTARE.md).

Pentru cele trei conturi, conversația prin Codex, vocea ElevenLabs și WhatsApp: [`docs/operations/RUNBOOK.md`](docs/operations/RUNBOOK.md). Această integrare rulează separat, local, fără publicarea site-ului.

Pe Windows, urmează [pornirea în PowerShell](docs/WINDOWS.md), fără `make`. Pentru voce și WhatsApp cu fișiere private, ghidul indică WSL2.

## Unde vezi produsul

- Consola dispecerului, publicată: https://daybreak.ghiseateodor245.workers.dev (pe planul gratuit Cloudflare, ecranele `/alerte` și `/rulare` pot da eroarea 1102; local merg toate).
- Pagina de prezentare (landing, în engleză): nu e publicată online. Local: `cd landing && bun install && bun dev`, apoi http://localhost:3730; sau `cd landing && bun run build` și `open landing/out/index.html` (merge fără server).

## Pornire rapidă

```bash
uv sync          # Python 3.12, toate dependențele
uv run cyberpunks run --scenario demo-vara  # circa 4 minute; testele cu datele complete au nevoie de această rulare
make check       # lint și teste
make validate-fixtures
```

Pașii completi de reproducere (date, antrenare, evaluare, demo), cu durata măsurată a fiecărui pas într-o clonă curată: [`docs/REPRODUCERE.md`](docs/REPRODUCERE.md). Întrebările tehnice probabile ale juriului, cu răspunsuri: [`docs/QA-JURIU.md`](docs/QA-JURIU.md).
