# Bilanț pe post: cifrele pentru prezentare

SIMULARE pe date publice, gândită pentru datele PPC. Sursa: `reports/bilant/metrics.json` (bilant-lgbm@a1862c1), comanda `make bilant-data bilant-eval`. Test: cele 300 de posturi ale hărții (registrul C), rețele nevăzute la antrenare; defectele de contor sunt cele ale firului A.

**Baza legală:** Codul de măsurare ANRE (Ord. 103/2015) cere ca sistemele de măsurare inteligentă să permită „cel puţin un contor de balanţă la fiecare post de transformare, pentru a facilita identificarea pierderilor tehnice şi netehnice”.

## 1. Ce vede doar bilanțul (cifra principală)

Contoarele clienților (modelul A) nu au cum să vadă aceste probleme: A găsește 0 prin construcție.

| Problema | Bilanțul găsește postul | și cauza corectă | Energia lipsă găsită |
|---|---|---|---|
| furt înainte de contor | 76% | 62% | 87% |
| pierderi în cabluri sau faze dezechilibrate | 64% | 50% | 86% |
| contorul postului setat greșit | 99% | 98% | doar pe hârtie |
| client trecut în bază la alt post | 58% | 54% | 75% |

- **Bilanțul găsește 84% din energia pierdută din aceste cauze, ~24.663 lei pe lună** pe cele 300 de posturi (la 0,70 lei/kWh, `config/economics.yaml`). Din posturile marcate, 18% sunt de fapt normale.
- În ziua demo, **48% din energia pierdută peste normal nu apare la niciun contor de client**.
- Diagnosticul cauzei: F1 macro 0,75 față de 0,48 la tabelul de reguli din concept.
- **Contorul martor** (regulă, prag 0,5% = clasa de exactitate): pe posturile cu martor prinde 98% din contoarele de balanță setate greșit, cu 0 alarme false; diferența normală martor − contor de balanță are mediana 0,06% (mentorul PPC: ~0,1%).

## 2. Cu bilanț față de fără, la verificările de contoare

Testul: harta (cele 300 de posturi, defectele de contor ale lui A apărute în ultimele 2-12 zile), ultimele 50 de zile, scoruri de tip A simulate (AUC 0,91). Regula v2 are parametrii căutați automat pe un lot separat de 3.000 de posturi (`reports/bilant/fusion_v2_params.json`) și doar confirmă: nu coboară niciodată un contor găsit de A.

| K verificări pe zi | Precizia: A singur → regula v1 → regula v2 | Deplasări degeaba evitate pe zi (v2 față de A) | Lei recuperați pe zi: A singur → v2 |
|---|---|---|---|
| 10 | 80% → 78% → **90%** | 1,0 | 4.966 → 8.278 |
| 20 | 64% → 62% → **68%** | 0,8 | 7.917 → 10.444 |
| 50 | 44% → 40% → **46%** | 1,0 | 11.716 → 13.595 |
| 100 | 31% → 29% → **33%** | 2,0 | 13.818 → 17.484 |

Cu scorurile **reale** ale lui A (ziua demo, 15.850 de contoare): AUC 0,917 (A singur), 0,916 (v1), 0,919 (v2); precizia în primele 500: 96,2% → 96,0%. Pe scorurile reale, A e deja precis în vârf; regula v2 nu strică, regula v1 strica la K mare.

## 3. Unde montăm întâi contoarele de balanță (planul B)

`reports/bilant/plan_b.md`: gradul de integrare a contoarelor inteligente e 56-67% pe regiuni (31 dec. 2025). Montând contoare de balanță la 20% din posturi, în ordinea modelului, găsim mai multă energie lipsă decât la întâmplare sau la „posturile mari întâi”.

## 4. Postul pentru demo

- **PT-1269** (`A-20250708-PT-1269`): pierderea pe cabluri e de 2,4 ori normalul, iar bilanțul estimează că o fază are ~71% din case. Adevărul din simulare și potrivirea cu lucrarea lui C (`C-20250708-PT-1269`, `phase_rebalance` prima treaptă) sunt în `reports/bilant/demo_posts.md`.
- Postul PT-1269: ~5402 lei pe lună pierduți peste normal. Cauza probabilă (97%): pierdere tehnică (cablu, faze dezechilibrate). Recomand: echipa de rețea (cabluri, îmbinări, faze).
