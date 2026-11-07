# Bilanț pe post: cifrele pentru prezentare

SIMULARE pe date publice, gândită pentru datele PPC. Sursa: `reports/bilant/metrics.json` (bilant-lgbm@89f184f), comanda `make bilant-data bilant-eval`. Test: cele 300 de posturi ale hărții (registrul C), rețele nevăzute la antrenare; defectele de contor sunt cele ale firului A.

**Baza legală:** Codul de măsurare ANRE (Ord. 103/2015) cere ca sistemele de măsurare inteligentă să permită „cel puţin un contor de balanţă la fiecare post de transformare, pentru a facilita identificarea pierderilor tehnice şi netehnice”.

## 1. Ce vede doar bilanțul (cifra principală)

Contoarele clienților (modelul A) nu au cum să vadă aceste probleme: A găsește 0 prin construcție.

| Problema | Bilanțul găsește postul | și cauza corectă | Energia lipsă găsită |
|---|---|---|---|
| furt înainte de contor | 74% | 54% | 85% |
| pierderi în cabluri sau faze dezechilibrate | 64% | 43% | 94% |
| contorul postului setat greșit | 99% | 98% | doar pe hârtie |
| client trecut în bază la alt post | 54% | 41% | 72% |

- **Bilanțul găsește 85% din energia pierdută din aceste cauze, ~24.969 lei pe lună** pe cele 300 de posturi (la 0,70 lei/kWh, `config/economics.yaml`). Din posturile marcate, 14% sunt de fapt normale.
- În ziua demo, **48% din energia pierdută peste normal nu apare la niciun contor de client**.
- Diagnosticul cauzei: F1 macro 0,70 față de 0,48 la tabelul de reguli din concept.
- **Contorul martor** (regulă, prag 0,5% = clasa de exactitate): pe posturile cu martor prinde 98% din contoarele de balanță setate greșit, cu 0 alarme false; diferența normală martor − contor de balanță are mediana 0,06% (mentorul PPC: ~0,1%).

## 2. Cu bilanț față de fără, la verificările de contoare

Bilanțul doar confirmă (urcă scorul contorului când lipsa de la post crește cât lipsește la contor); nu coboară niciodată un contor găsit de A.

| Modelul de contoare | K verificări pe zi | Precizia fără → cu | Deplasări degeaba evitate pe zi | Lei recuperați pe zi fără → cu |
|---|---|---|---|---|
| scor A simulat, calitatea pe Londra (AUC 0,91) | 10 | 10,2% → 12,0% | 0,17 | 824 → 862 |
|  | 20 | 6,4% → 8,0% | 0,33 | 921 → 1.065 |
|  | 50 | 4,0% → 4,5% | 0,25 | 1.177 → 1.457 |
|  | 100 | 2,6% → 2,7% | 0,10 | 1.370 → 1.616 |
| scor A simulat, calitatea pe SGCC (AUC 0,80) | 10 | 2,5% → 3,8% | 0,12 | 126 → 445 |
|  | 20 | 1,4% → 2,5% | 0,23 | 126 → 490 |
|  | 50 | 0,9% → 1,4% | 0,25 | 450 → 604 |
|  | 100 | 0,8% → 1,1% | 0,33 | 539 → 746 |
| scorurile REALE ale lui A, ziua demo | 10 | 100,0% → 100,0% | 0 | - |
|  | 100 | 100,0% → 100,0% | 0 | - |
|  | 300 | 100,0% → 100,0% | 0 | - |
|  | 500 | 96,2% → 87,4% | -44 | - |

Cum se citește: cu scorurile reale, A e deja precis în vârful listei, iar bilanțul nu mai adaugă nimic la clasare. Când modelul de contoare e mai slab, confirmarea din bilanț ridică banii recuperați (la calitatea SGCC, de 3,5 ori în primele 10).

## 3. Unde montăm întâi contoarele de balanță (planul B)

`reports/bilant/plan_b.md`: gradul de integrare a contoarelor inteligente e 56-67% pe regiuni (31 dec. 2025). Montând contoare de balanță la 20% din posturi, în ordinea modelului, găsim mai multă energie lipsă decât la întâmplare sau la „posturile mari întâi”.

## 4. Postul pentru demo

- **PT-1269** (`A-20250708-PT-1269`): pierderea pe cabluri e de 2,4 ori normalul, iar bilanțul estimează că o fază are ~71% din case. Adevărul din simulare și potrivirea cu lucrarea lui C (`C-20250708-PT-1269`, `phase_rebalance` prima treaptă) sunt în `reports/bilant/demo_posts.md`.
- Postul PT-1269: ~5402 lei pe lună pierduți peste normal. Cauza probabilă (peste 99%): pierdere tehnică (cablu, faze dezechilibrate). Recomand: echipa de rețea (cabluri, îmbinări, faze).
