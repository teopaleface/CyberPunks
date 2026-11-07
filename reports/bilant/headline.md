# Bilanț pe post: cifrele pentru prezentare

SIMULARE pe date publice, gândită pentru datele PPC. Sursa: `reports/bilant/metrics.json` (bilant-lgbm@18dd150), comanda `make bilant-data bilant-eval`. Test: cele 300 de posturi ale hărții (registrul C), rețele nevăzute la antrenare; defectele de contor sunt cele ale firului A.

## 1. Ce vede doar bilanțul (cifra principală)

Contoarele clienților (modelul A) nu au cum să vadă aceste probleme: A găsește 0 prin construcție.

| Problema | Bilanțul găsește postul | și cauza corectă | Energia lipsă găsită |
|---|---|---|---|
| furt înainte de contor | 74% | 55% | 86% |
| pierderi în cabluri sau faze dezechilibrate | 65% | 42% | 95% |
| contorul postului setat greșit | 99% | 99% | doar pe hârtie |
| client trecut în bază la alt post | 50% | 30% | 70% |

- **Bilanțul găsește 85% din energia pierdută din aceste cauze, ~25.010 lei pe lună** pe cele 300 de posturi (la 0,70 lei/kWh, `config/economics.yaml`). Din posturile marcate, 13% sunt de fapt normale.
- În ziua demo, **48% din energia pierdută peste normal nu apare la niciun contor de client**.
- Diagnosticul cauzei: F1 macro 0,67 față de 0,48 la tabelul de reguli din concept.

## 2. Cu bilanț față de fără, la verificările de contoare

Bilanțul doar confirmă (urcă scorul contorului când lipsa de la post crește cât lipsește la contor); nu coboară niciodată un contor găsit de A.

| Modelul de contoare | K verificări pe zi | Precizia fără → cu | Deplasări degeaba evitate pe zi | Lei recuperați pe zi fără → cu |
|---|---|---|---|---|
| scor A simulat, calitatea pe Londra (AUC 0,91) | 10 | 10,2% → 12,2% | 0,20 | 824 → 855 |
|  | 20 | 6,4% → 7,8% | 0,28 | 921 → 1.000 |
|  | 50 | 4,0% → 4,5% | 0,28 | 1.177 → 1.458 |
|  | 100 | 2,6% → 2,7% | 0,05 | 1.370 → 1.587 |
| scor A simulat, calitatea pe SGCC (AUC 0,80) | 10 | 2,5% → 4,0% | 0,15 | 126 → 456 |
|  | 20 | 1,4% → 2,6% | 0,25 | 126 → 502 |
|  | 50 | 0,9% → 1,4% | 0,25 | 450 → 602 |
|  | 100 | 0,8% → 1,1% | 0,40 | 539 → 740 |
| scorurile REALE ale lui A, ziua demo | 10 | 100,0% → 100,0% | 0 | - |
|  | 100 | 100,0% → 100,0% | 0 | - |
|  | 300 | 100,0% → 100,0% | 0 | - |
|  | 500 | 93,0% → 90,6% | -12 | - |

Cum se citește: cu scorurile reale, A e deja precis în vârful listei, iar bilanțul nu mai adaugă nimic la clasare. Când modelul de contoare e mai slab, confirmarea din bilanț ridică banii recuperați (la calitatea SGCC, de 3,6 ori în primele 10).

## 3. Unde montăm întâi contoarele de bilanț (planul B)

`reports/bilant/plan_b.md`: gradul de integrare a contoarelor inteligente e 56-67% pe regiuni (31 dec. 2025). Montând contoare de bilanț la 20% din posturi, în ordinea modelului, găsim mai multă energie lipsă decât la întâmplare sau la „posturile mari întâi”.

## 4. Postul pentru demo

- **PT-1269** (`A-20250708-PT-1269`): pierderea pe cabluri e de 2,2 ori normalul, iar bilanțul estimează că o fază are ~69% din case. Adevărul din simulare și potrivirea cu lucrarea lui C (`C-20250708-PT-1269`, `phase_rebalance` prima treaptă) sunt în `reports/bilant/demo_posts.md`.
- Postul PT-1269: ~5146 lei pe lună pierduți peste normal. Cauza probabilă (99%): pierdere tehnică (cablu, faze dezechilibrate). Recomand: echipa de rețea (cabluri, îmbinări, faze).
