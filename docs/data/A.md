# Firul A: contoare defecte sau manipulate (date, model, reproducere)

Ce face: din consumul contoarelor inteligente, modelul nostru găsește contoarele **defecte** (oprite, blocate, fără comunicație, cu salturi false, cu ceasul decalat, cu citiri negative, care înregistrează tot mai puțin) și pe cele **manipulate** (furt), estimează energia pierdută în lei și recomandă ce să facă echipa mâine: verificare la fața locului, citire la distanță, urmărire sau decizia unui om.

## Reproducere (din rădăcina repo-ului)

```bash
uv sync
make a-predict      # lucrările pentru demo-vara și maine, din modelul și pachetul demo din git (~10 s)
make a-all          # totul de la zero: descărcare (~260 MB), features, antrenare, evaluare, lucrări (~5 min)
make a-test         # testele firului A
```

Pașii din `make a-all`, separat:

| Pas | Comandă | Ce scrie |
|---|---|---|
| Descărcare cu sume de control | `uv run python -m cyberpunks.a_contoare.download` | `data/raw/A/` (în afara git); sumele LCL în `data/samples/A/checksums_lcl.sha256` |
| Features SGCC | `uv run python -m cyberpunks.a_contoare.sgcc` | `data/processed/A/sgcc_features.parquet` |
| Eșantioane Londra cu probleme injectate | `uv run python -m cyberpunks.a_contoare.lcl` | `data/interim/A/`, `data/processed/A/lcl_samples.parquet` |
| Antrenare | `uv run python -m cyberpunks.a_contoare.train` | `models/A/a-lgbm.joblib`, `models/A/a-lgbm-sgcc.joblib` |
| Evaluare pe test separat | `uv run python -m cyberpunks.a_contoare.evaluate` | `reports/A/metrics.json`, `reports/A/metrics_full.json`, `reports/A/figures/` |
| Lucrări pentru planificator | `uv run python -m cyberpunks.a_contoare.predict --scenario demo-vara` | `outputs/work_items/<s>/A.jsonl`, `outputs/series/<s>/<id>.json`, `A_summary.json`, `A_ground_truth.csv` |
| Robustețe (date lipsă, SGCC pe timp) | `uv run python -m cyberpunks.a_contoare.robustness` | `reports/A/robustness.json` |
| Alegerea features pe calibrare | `uv run python -m cyberpunks.a_contoare.select_features` | `reports/A/feature_selection.json` |
| Analiza erorilor și model card | `uv run python -m cyberpunks.a_contoare.report` | `reports/A/error_analysis.md`, `reports/A/model_card.md` |
| Ce intră în git pentru demo | `uv run python -m cyberpunks.a_contoare.train --release` | `models/release/A/a-lgbm.joblib`, `data/samples/A/demo_pack.*`, `data/samples/A/similar_ref.parquet` |

Din cod: `from cyberpunks.a_contoare.predict import run; run("demo-vara", None)` întoarce calea fișierului `A.jsonl`. Seed-urile sunt fixe, iar LightGBM rulează determinist, pe 4 nuclee.

## Datele

| Set | Ce conține | Licență | Cum îl folosim |
|---|---|---|---|
| **SGCC** (State Grid Corporation of China), [repo](https://github.com/henryRDlab/ElectricityTheftDetection), Zheng et al. 2018, IEEE TII, DOI 10.1109/TII.2017.2785963 | 42.372 de clienți, consum zilnic 2014-01-01 - 2016-10-31, 3.615 marcați ca furt (etichete reale, câte una pe client) | fără licență explicită; se cere citarea articolului | doar pentru cercetare, nu îl redistribuim; în git sunt doar scriptul, sumele SHA-256 și metricile |
| **Low Carbon London** (UK Power Networks), [London Datastore](https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d) | consum real la 30 de minute; luăm fișierele 0-44 din arhiva partiționată (1.414 gospodării cu tarif fix, nov. 2011 - feb. 2014) | CC BY 4.0 | profile reale peste care injectăm probleme; atribuire: "Contains data from UK Power Networks, Low Carbon London project, via London Datastore, CC BY 4.0. Faults and theft patterns were injected synthetically by team CyberPunks." |
| **Registrul comun al posturilor** (firul C, `data/samples/C/posts.csv`) | 300 de posturi sintetice (PT-1001..PT-1300) în București-Ilfov, cu numărul de clienți (27.045 în total) | sintetic; poziții din OpenStreetMap (ODbL 1.0, © OpenStreetMap contributors) | posturile pe care stau contoarele A; aceleași cu C și cu bilanțul pe post |

Ce am verificat noi pe SGCC: coloanele de zile sunt în ordine alfabetică (le sortăm), lipsește ziua 2016-09-18 (o punem ca NaN), 25,6% valori lipsă, dar 30-42% pe trimestru în 2014-2015 și sub 2% în 2016. De aceea SGCC se împarte pe clienți, nu pe timp. Detalii: `docs/research/A.md`.

Curățarea Londra (`lcl.py`): spațiile și textul "Null" din valori, rândurile duplicate (inclusiv ora dublată la trecerea la ora de iarnă, mediate), orele care nu sunt fix :00 sau :30; ora din fișier marchează sfârșitul intervalului.

## Date SINTETICE (etichetate peste tot ca sintetice)

1. **Problemele injectate** (`inject.py`, determinist, cu seed). Furtul folosește atacurile h1-h6 din Jokar, Arianpoo, Leung 2016 (formulele din Nabil et al. 2018, arXiv 1809.01774), plus bypass parțial cu instalare treptată și furt de noapte. Defectele urmează familiile de verificări VEE din Oracle Utilities MDM: contor oprit, valoare blocată, goluri de comunicație (cu salt de recuperare), salturi false, ceas decalat, citiri negative și sub-înregistrare accelerată. Am adăugat două schimbări **normale**, concediul și schimbarea ocupanților, ca exemple grele: modelul nu trebuie să le semnaleze. Formulele și parametrii sunt în docstring-ul modulului.
2. **Rotunjirea la rezoluția contorului** (0,001 kWh) după fiecare injecție. Fără ea, injecțiile prin înmulțire dau valori pe care niciun contor nu le trimite. La prima versiune, modelul a învățat artefactul: semnala 46% din contoarele demo. După rotunjire semnalează 5-6%. Vezi analiza erorilor.
3. **Prevalența** (IPOTEZĂ, nu avem cifre publice bune): la antrenare 25% defecte și 20% furturi (ca modelul să aibă exemple); la calibrare, test și demo 3% defecte, 2% furturi și 4% schimbări normale. Precizia@K depinde de prevalență, deci o raportăm împreună cu ea.
4. **Topologia București-Ilfov** (`topology.py`): contoarele stau pe cele 300 de posturi din registrul comun al produsului (firul C). Pe fiecare post punem contoarele inteligente **integrate**: 58,81% din clienții postului, gradul de integrare din Muntenia la 31.12.2025 (infobuz, rezumat în `memory/12-probleme-reale-ppc-2026.md`). Ies 15.850 de contoare (8.526 în București, 7.324 în Ilfov), la 25-400 m de post, după tipul zonei. Contoarele sunt sintetice. Fișier: `data/samples/A/meters.csv`.
5. **Populația demo** (`demo.py`): fiecare contor primește profilul real al uneia dintre cele 160 de gospodării de **test** din pachetul demo (nevăzute la antrenare), cu scară aleatoare și variație pe zi. Calendarul se mută în 2026 cu un număr întreg de săptămâni, deci zilele săptămânii rămân la locul lor: 8 iulie 2025 corespunde zilei de 9 iulie 2013. Pe lângă probleme, injectăm câteva intrări greșite: 0,2% din contoare raportate în Wh și 0,3% cu istoric prea scurt. Adevărul se scrie separat (`A_ground_truth.csv`), doar pentru evaluare.

## Împărțirea (fără scurgeri)

- **SGCC:** pe clienți, stratificat: 60% antrenare (din care 15% pentru oprirea timpurie), 20% calibrare, 20% test. Referința "vecinilor" (mediana zilnică) vine doar din clienții de antrenare.
- **Londra:** gospodăriile se împart 60/20/20 (838 / 280 / 265), deci nicio gospodărie nu apare în două seturi. Antrenarea și calibrarea folosesc zile de evaluare din dec. 2012 - aug. 2013, testul din sept. 2013 - feb. 2014 (perioadă ulterioară). Un eșantion e o fereastră de 180 de zile; problema contează dacă e activă în ultimele 28.
- Calibrarea (Venn-ABERS) și pragurile conformal se potrivesc doar pe setul de calibrare.

## Features (fiecare cu motiv; lista completă în `features.py`, `FEATURE_INFO`)

- **Zilnice** (27, merg și pe SGCC): goluri (lungime, număr de goluri separate), zile cu zero, valori repetate, scăderea față de propriul istoric și față de vecini, cea mai mare scădere bruscă, panta (proprie și față de vecini), variația, forma distribuției, ritmul săptămânal, salturile, valorile negative, raportul față de vecinii de pe post, corelația cu vecinii, nivelul de consum.
- **Din citirile la 30 de minute** (13): ponderea consumului de noapte și schimbarea ei, asemănarea profilului zilei cu cel obișnuit, decalajul profilului (ceas decalat), profilul plat, vârful mutat, intervalele de exact zero, citirile negative, salturile, valorile repetate.
- Setul a fost ales pe o validare din setul de antrenare (gospodării ținute deoparte), nu pe calibrare și nu pe test (`select_features.py`).

## Modelul și deciziile

- **`a-lgbm`** (folosit de agent): LightGBM cu 3 clase (normal / defect / manipulare), ponderi pe clase, oprire timpurie validată pe gospodării separate. Scorul de problemă e calibrat Venn-ABERS (pe o grilă de cuantile, cu abaterea față de calculul exact măsurată) și are interval (`interval_low`, `interval_high`).
- **"Nu sunt sigur":** conformal Mondrian pe scorul brut al modelului, cu pragurile alese pe calibrare (α = 1% pentru "normal", 30% pentru "problemă"). Acoperirea mulțimii de predicție (empirică, măsurată pe test, pentru că ferestrele de calibrare repetă gospodăriile): conține "normal" pentru ~99% din contoarele normale și "problemă" pentru ~70% din problemele reale. Asta nu înseamnă că 70% din probleme sunt recunoscute sigur: o parte cad în zona gri (ambele clase în mulțime). Acolo lucrarea are `abstain=True`, cu motivul scris, și merge la `human_review`. La om ajung și contoarele cu istoric prea scurt, cu prea puține date recente sau cu unitate de măsură suspectă (`validate.py`). Câte contoare normale ajung efectiv la echipă sau la om se măsoară pe demo și e raportat în `reports/A/error_analysis.md`, secțiunea 7.
- **Consum mic** (etică): un furt suspectat la un contor din chintila de jos a consumului merge întâi la un om. Poate fi o locuință goală sau sărăcie energetică, nu furt.
- **Valoarea** (`config/economics.yaml`, cheia `meters`): kWh lipsă pe zi față de normal (propriul istoric, mutat după sezonul vecinilor) × 90 de zile × 0,70 lei/kWh. La un contor defect se adaugă o vizită evitată (citire manuală sau reclamație), egală cu costul vizitei. `expected_value_lei = score × value_if_true_lei`.
- **Recomandarea** (decizia finală o ia planificatorul): furt sigur → verificare la fața locului (cu `safety_flag`); defect sigur → verificare sau, dacă golurile sunt recente și scorul mai mic, citire la distanță întâi; contor fără comunicație → verificare (`extra.smart_meter=false`); următoarele 40 → urmărire.
- **`a-lgbm-sgcc`**: același tip de model, binar, pe SGCC. Arată cât valorează aceleași features pe etichete reale de furt.

## Ieșirile pentru planificator

- `outputs/work_items/<s>/A.jsonl`: ~250 de lucrări pe zi: cele mai valoroase 150 sigure, 40 de urmărit, cazurile nesigure și cele cu date insuficiente. Câmpuri în `extra`: `series_ref`, `p_faulty`, `p_tamper`, `conformal`, `post_id`, `estimated_kwh_lost_per_day`, `rule_vee_fired` (dacă regula simplă l-ar fi prins), `smart_meter`, `comm_down`, `level_kwh_day`, `low_consumption_guard`.
- `outputs/series/<s>/<id>.json`: consumul zilnic pe 60 de zile, ce ar fi fost normal (P10, P50, P90) și zilele marcate (zero, gol, salt, negativ, plat).
- `outputs/work_items/<s>/A_summary.json`: cifrele zilei (contoare evaluate, semnalate, nesigure, precizia față de adevărul injectat).

## Cifrele (din `reports/A/metrics_full.json`, refăcute de `make a-evaluate`)

Toate cifrele, cu tabele, sunt în `reports/A/error_analysis.md` și `reports/A/model_card.md`, generate de `make a-report`. Pe scurt, la K = 1% din contoare:
- SGCC (etichete reale, 8.475 de clienți nevăzuți): precizia@K 0,81, față de 0,04 la regula simplă, 0,11 la regula VEE completă și 0,19 la IsolationForest. ROC-AUC 0,82.
- Londra (probleme injectate): precizia@K 1,00 (regula VEE: 0,61). Cifra vine din defectele evidente care umplu vârful listei; la K = numărul de probleme, precizia e 0,64.
- Doar problemele subtile: 0,69, față de 0,02 la VEE.
- Fără scurgeri: cu etichete amestecate, PR-AUC cade la prevalență.
