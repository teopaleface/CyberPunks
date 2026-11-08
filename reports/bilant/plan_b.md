# Planul B: unde montăm întâi contoarele de balanță

SIMULARE pe date publice, gândită pentru datele PPC. Comanda: `uv run python -m cyberpunks.a_bilant.planb` (după `make bilant-data bilant-eval`).

## De ce contează

Gradul de integrare a contoarelor inteligente la 31 decembrie 2025 (infobuz, prin `memory/12-probleme-reale-ppc-2026.md`): Dobrogea 66,85%, Muntenia 58,81%, Banat 56,45%. Ținta RER e 67% la finalul lui 2026. Planul de dezvoltare RER 2026-2035 cere ca infrastructura de contorizare inteligentă să permită cel puțin un contor de balanță în fiecare post (`docs/research/bilant_lit.md`). Până atunci, o parte din posturi nu au bilanț complet. Concentratorul de date din post nu e contor de balanță. Planul B răspunde la întrebarea: unde montăm întâi?

## Cum

1. Fără contor de post, energia intrată se estimează din modelul rețelei: suma clienților plus pierderea normală estimată fără istoric (`normal_cold`, eroare medie 12,0 kWh/zi pe rețele nevăzute, `reports/bilant/metrics.json`).
2. Un model (LightGBM, pierdere Huber) învață, pe cele 300 de posturi de antrenare care au contor de balanță, lipsa măsurată peste normal din ultimele 90 de zile. Folosește doar ce se vede fără contorul postului: semnalele contoarelor de client (zile cu zero, blocate, negative noaptea, clienți cu consum scăzut la jumătate, cel mai mare consum dispărut), mărimea postului, cablurile din GIS și pierderea tehnică estimată.
3. Pe cele 287 posturi ale hărții (fără cele cu contorul de post setat greșit, care nu există unde nu e contor), comparăm ce parte din lipsa reală totală (din construcție) se găsește montând contoare la primele k posturi.

## Rezultat

| metoda | primele 29 posturi (10%) | primele 57 posturi (20%) | primele 95 posturi (33%) | primele 126 posturi (44%) |
|---|---|---|---|---|
| model (planul B) | 19.4% | 30.3% | 46.0% | 55.2% |
| posturile mari întâi | 15.2% | 22.6% | 39.9% | 45.5% |
| pierderea tehnică estimată întâi | 18.4% | 27.1% | 52.2% | 60.7% |
| la întâmplare (media a 200 de trageri) | 10.3% | 19.8% | 33.2% | 44.4% |

- Cu modelul, primele 20% din posturi (57) acoperă **30%** din energia lipsă, față de 20% la întâmplare și 23% la „posturile mari întâi”.
- Un contor de balanță montat după clasament găsește în medie ~2,997 lei pe an de energie lipsă (la 0.7 lei/kWh, `config/economics.yaml`), față de ~1,962 lei pe an la un post ales la întâmplare.
- Clasamentul complet: `reports/bilant/plan_b_ranking.csv`; curbele: `reports/bilant/plan_b.png`.

## Limite

- Furtul înainte de contor nu lasă urme la contoarele clienților. Planul B îl găsește doar prin mărimea și tipul postului, de aceea pierde din ce găsește bilanțul complet.
- Lipsa reală e din construcție (simulare). Pe date PPC, eticheta de antrenare e lipsa măsurată la posturile care au deja contor de balanță, exact ca aici (`measured_excess`).
