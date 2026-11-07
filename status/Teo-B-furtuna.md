# Status: Teo-B-furtuna
Actualizat: 2026-11-07 12:58
Milestone curent: M0
Gata de merge: nu

## Făcut
- 12:44 Citit `memory/INDEX.md`, `07-tema-ppc.md`, `08-ppc-workshop-ai.md`, `docs/PLAN.md`, `docs/CONTRACTS.md`, `contracts.py`, fixture-urile.
- 12:46 `uv sync` și `make check` trec (7 teste).
- 12:47 Faza 0 pornită: 4 subagenți în paralel (zi reală de furtună în România; literatură și surse meteo; detalii EAGLE-I; clienți și fiabilitate Rețele Electrice).
- 12:50 EAGLE-I verificat prin API-ul figshare: versiunea 4 (25 feb. 2026) acoperă 2014-2025, CC BY 4.0, 1,1-1,4 GB pe an. Descărcate DQI, MCC, coverage_history.

## Urmează
- Scriptul de descărcare cu sume de control, descărcarea anilor 2018-2025 pornită în fundal.
- `docs/research/B.md` din rapoartele subagenților (până la 14:30).
- Data reală pentru `demo-vara` (până la 15:00).
- M1 (17:30): tabelul comitat × zi, baseline-uri, primul LightGBM, `metrics.json`, `B.jsonl` pentru `demo-vara` și `maine`.

## Blocaje
- Niciunul.

## Cereri către orchestrator
- (vine până la 15:00) data reală pentru `demo-vara`.

## Cum se rulează (comenzile exacte)
- (vine la M1)

## Cifre (doar din scripturi, cu comanda)
- (vine la M1)

## Decizii (cu ora)
- 12:50 Folosim EAGLE-I v4 de pe figshare (2014-2025), nu doar 2014-2022.
