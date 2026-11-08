# CyberPunks: Daybreak

**Evaluarea ML:** [raportul comun — date, modele, baseline, Optuna, CatBoost/XGBoost și teste](reports/ml/README.md).
Verificare reproductibilă: `uv sync --group bench` și `make ml-check`.

Proiectul echipei CyberPunks la SmartHack XI 2026 (7-8 noiembrie, București), pe tema PPC "24h to Power PPC": un agent AI care decide unde merg mâine echipele de teren Rețele Electrice, pe baza a trei modele ML antrenate de echipă (contoare defecte sau manipulate, risc de avarii la furtună, tensiune prea mare din cauza prosumatorilor), și explică fiecare decizie.

Stare: în lucru, vezi [`status/ACUM.md`](status/ACUM.md). Planul: [`docs/PLAN.md`](docs/PLAN.md). Formatele de date: [`docs/CONTRACTS.md`](docs/CONTRACTS.md). Contextul și research-ul: [`memory/`](memory/INDEX.md).

## Cum testezi

Aplicația completă, cu conturi și baza operațională locală, rulează pe **http://127.0.0.1:3870/app**. Pentru un laptop nou, urmați secțiunea [Pornire pe alt laptop, din main](docs/operations/RUNBOOK.md#pornire-pe-alt-laptop-din-main). Conturile și baza locală nu se transferă prin `git pull`.

Ghidul pentru echipă, cu pornirea demo-ului într-o singură comandă (`make demo`) și ce verifici pe fiecare ecran: [`docs/TESTARE.md`](docs/TESTARE.md).

Pentru cele trei conturi, conversația prin Codex, vocea ElevenLabs și WhatsApp: [`docs/operations/RUNBOOK.md`](docs/operations/RUNBOOK.md). Această integrare rulează separat, local, fără publicarea site-ului.

Pe Windows, urmează [pornirea în PowerShell](docs/WINDOWS.md), fără `make`. Pentru voce și WhatsApp cu fișiere private, ghidul indică WSL2.

## Pornire rapidă

```bash
uv sync          # Python 3.12, toate dependențele
make check       # lint și teste
make validate-fixtures
```

Pașii completi de reproducere (date, antrenare, evaluare, demo), cu durata măsurată a fiecărui pas într-o clonă curată: [`docs/REPRODUCERE.md`](docs/REPRODUCERE.md). Întrebările tehnice probabile ale juriului, cu răspunsuri: [`docs/QA-JURIU.md`](docs/QA-JURIU.md).
