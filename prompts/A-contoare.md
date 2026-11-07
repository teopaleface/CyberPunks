# Firul A: contoare defecte sau manipulate

Branch: `Teo-A-contoare`. Status: `status/Teo-A-contoare.md`.

## Ce deții

`src/cyberpunks/a_contoare/`, `tests/a/`, `reports/A/`, `docs/data/A.md`, `docs/research/A.md`, `data/samples/A/`, secțiunea A din `Makefile`, `status/Teo-A-contoare.md`.

## De ce contează pentru PPC

- PPC are peste 2 milioane de contoare inteligente în România, fiecare cu 96 de citiri pe zi (circa 192 de milioane de rânduri pe zi). Pe slide-ul lor: "What comes next: AI. Anomaly detection on meter behaviour, predictive monitoring of faulty meters."
- PDF-ul temei: "ce clienți trebuie verificați", "detecție de anomalii cu etichete puține", "clasificare pe date dezechilibrate", "ranking sub constrângeri de capacitate", "un scor de anomalie de 0,87 nu îi spune unui tehnician unde să meargă mâine dimineață".
- PPC are deja Energy Anomaly Detection pentru furt, în producție. Diferența noastră: contoarele DEFECTE (blocate, zero, goluri, salturi, derivă) pe lângă manipulare, energia pierdută estimată și decizia de după (vizită, citire la distanță, urmărire, om).

## Faza 0: cercetare (cel mult 45 de minute, subagenți în paralel), scrisă în `docs/research/A.md`

1. Setul SGCC: https://github.com/henryRDlab/ElectricityTheftDetection (`data.zip`, `data.z01`, `data.z02`, circa 52 MB, arhivă împărțită). Verifică structura reală (coloanele, eticheta FLAG, perioada 2014-01-01..2016-10-31, 42.372 de clienți, 3.615 marcați ca furt, circa 25% valori lipsă) și licența (repo-ul nu are licență explicită; caută sursa originală și copii cu licență, de exemplu Kaggle `bensalem14/sgcc-dataset`). Decide cum îl folosești și scrie riscul.
2. Contoarele din Londra, Low Carbon London: https://data.london.gov.uk/dataset/smartmeter-energy-use-data-in-london-households. Licența exactă, mărimea, formatul, link-urile directe, rezoluția de 30 de minute. Dacă e prea mare, un subset documentat (de exemplu 1.000 de locuințe pe un an).
3. Modele de manipulare din literatură pentru date sintetice etichetate: Jokar, Arianpoo, Leung (2016), atacurile h1-h6. Plus tipare de contor defect: zero, blocat (valoare constantă), goluri de comunicație, salturi, derivă de ceas, valori negative, citiri dublate. Formule și parametri.
4. Rezultatele raportate pe SGCC în literatură (de exemplu Wide & Deep CNN, Zheng et al. 2018), ca reper cinstit.
5. Calibrare (isotonic) și conformal prediction pentru "nu sunt sigur".

## Ce construiești

- Descărcare cu sume de control: `uv run python -m cyberpunks.a_contoare.download`.
- Date: SGCC (etichete reale de furt, zilnic) plus contoarele din Londra cu defecte și manipulări injectate de noi (etichete din construcție, cu tipul defectului). Împărțire pe clienți și pe timp, fără scurgeri între train și test. Generatorul sintetic stă în repo și e documentat în `docs/data/A.md`.
- Topologie sintetică: contoarele grupate pe posturi de transformare (pentru comparația cu vecinii) și circa 10.000 de contoare plasate în București-Ilfov (bbox în `config/area.yaml`). Poți folosi clădiri sau posturi din OpenStreetMap (ODbL, cu atribuire). Totul etichetat sintetic.
- Features, fiecare cu un motiv scris: șiruri de zile cu zero, porțiuni plate, goluri, salturi, raportul noapte/zi, abaterea față de propriul istoric (mediană mobilă), raportul față de vecinii de pe post, schimbări bruște de nivel, sezonalitatea.
- Baseline-uri: (1) regulă simplă (zero cel puțin N zile sau scădere de cel puțin 50% față de propriul istoric); (2) IsolationForest.
- Model: LightGBM (multiclasă normal / defect / manipulare, sau două modele binare), cu ponderi pentru clase, calibrare și conformal prediction. Opțional, un challenger 1D-CNN pe SGCC.
- Evaluare pe test separat (clienți nevăzuți și perioadă ulterioară): PR-AUC, ROC-AUC, precizie@K și recall@K pentru K egal cu capacitatea echipelor, valoarea capturată@K în lei, calibrare (Brier, diagramă), recall pe fiecare tip de defect. Script: `uv run python -m cyberpunks.a_contoare.evaluate`, care scrie `reports/A/metrics.json` (contractul `ModelReport`) și figurile.
- Analiza erorilor (`reports/A/error_analysis.md`): pe tipuri de defect, pe nivel de consum, pe lipsa datelor, plus ce ai încercat ca să corectezi. Atenție la etică: consumul mic poate însemna sărăcie energetică, nu furt. Verifică rata de alarme false pe chintile de consum și spune cum o limitezi.
- Robustețe: validarea intrărilor (valori negative, salturi peste puterea contractată, timestamp-uri dublate, Wh în loc de kWh, ora de vară), goluri, istoric prea scurt: `abstain` cu motiv.
- Explicabilitate: SHAP (TreeExplainer), top factori cu `label_ro` în cuvinte simple; cazuri similare din istoric (vecini apropiați pe features, cu rezultatul confirmat).
- Valoare: kWh pierduți estimați (față de propriul istoric sau de vecini) × preț × orizont, din `config/economics.yaml` (cheia `meters`). `expected_value_lei = score × value_if_true_lei`.
- Ieșirea: `uv run python -m cyberpunks.a_contoare.predict --scenario <s> --date <YYYY-MM-DD>` scrie `outputs/work_items/<s>/A.jsonl` (WorkItem valid) și `outputs/series/<s>/<work_item_id>.json` (contractul `Series`: consumul cu ce ar fi fost normal și anomaliile marcate). Recomandări posibile: `inspect_on_site`, `remote_reading`, `watchlist`, `human_review`.
- Expune și o funcție Python pe care planificatorul o poate importa: `cyberpunks.a_contoare.predict.run(scenario: str, date: str) -> pathlib.Path` (calea fișierului JSONL).
- Model card: `reports/A/model_card.md` (date, limite, utilizare corectă, etică).

## Milestones (ora României)

- 14:30 M0: `docs/research/A.md`, date descărcate, status completat.
- 17:30 M1: baseline și primul LightGBM, `metrics.json` valid, `A.jsonl` valid pentru scenariile `demo-vara` și `maine` (până anunță B data, folosește orice dată de vară și fă data un parametru).
- 21:30 M2: modelul bate baseline-ul pe metrica principală (precizie@K sau PR-AUC, alege și justifică), calibrare, conformal, SHAP.
- 03:00 M3: analiza erorilor, teste de robustețe în `tests/a/`, cazuri similare, verificarea alarmelor false pe consum mic.
- 08:00 M4: model card, comenzi reproductibile în README-ul tău de secțiune (`docs/data/A.md`), curățenie.
