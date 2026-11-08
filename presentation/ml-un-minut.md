# Partea de ML într-un minut (Eden, pagina Agent)

Ecranul: site-ul, pagina **Agent**, secțiunea **„Four models, one plan”** (`/agent#models`). Patru carduri: Meters, Storms, Voltage, Energy balance. Cifrele de pe carduri se citesc din cardurile modelelor (`web/site/src/data/daybreak.json`), aceleași ca în rapoarte.

Aproximativ 150 de cuvinte, adică un minut vorbit liniștit. Pe fiecare card arăți cu mouse-ul bara colorată (modelul) față de bara gri (reperul simplu).

| Când | Card | Ce spui |
|---|---|---|
| 0:00-0:08 | Titlul | „În spatele agentului sunt patru modele antrenate de noi, toate LightGBM. Fiecare e testat pe date pe care nu le-a văzut și comparat cu o metodă simplă.” |
| 0:08-0:22 | **Meters** (contoare) | „Contoare: consum real din Londra, cu defecte injectate de noi, plus setul SGCC, cu furturi reale. Agentul trimite echipele la primul 1% din contoare. Acolo precizia e 0,63, față de 0,07 la regula simplă. Pe furturile reale, PR-AUC 0,40 față de 0,08.” |
| 0:22-0:35 | **Storms** (furtuni) | „Furtuni: avarii reale din SUA, EAGLE-I, plus vremea de la Open-Meteo. Prezice riscul de avarie pe zonă pentru a doua zi. Pe 2025, an nevăzut: PR-AUC 0,28 față de 0,18 la regula pe rafale de vânt.” |
| 0:35-0:46 | **Voltage** (C, tensiune) | „Tensiune: rețele SimBench, etichete calculate cu fluxul de putere. Modelul înlocuiește calculul de un minut cu unul sub o zecime de secundă. Eroarea e de patru ori mai mică decât la un model liniar.” |
| 0:46-0:56 | **Energy balance** (bilanț) | „Bilanț pe post: estimează pierderea normală și cauza pierderii în plus, pe 300 de posturi noi. F1 0,75 față de 0,48 la tabelul de reguli.” |
| 0:56-1:00 | Nota de sub carduri | „Am încercat și CatBoost și XGBoost pe aceleași teste. Niciunul nu a bătut LightGBM.” |

## Dacă întreabă juriul

- **Ce e sintetic?** La C și la bilanț etichetele sunt simulate: fluxul de putere, respectiv cauzele ascunse de noi. Profilele de consum și vremea sunt reale. Pe carduri scrie „Synthetic labels”.
- **De ce PR-AUC și nu acuratețe?** Clasele sunt rare (o avarie mare apare în ~10% din zone-zile, un contor defect e și mai rar). Acuratețea ar fi mare și la un model care spune mereu „nu”.
- **Unde se vede scăderea?** La contoare, precizia în top 1% pe SGCC scade de la 0,80 la 0,40 când testul e separat în timp. La furtuni, pe datele din România (Powercut, 520 de zone-zile, fără furtuni severe), modelul nu bate regula pe rafale. Detalii: `reports/A/robustness.json`, `reports/B/romania_eval.md`.
- **Cum se reproduce?** Comanda pentru fiecare model e în cardul lui, câmpul `reproduce`; benchmarkul CatBoost/XGBoost: `reports/benchmark/RAPORT.md`.
