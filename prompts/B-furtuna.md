# Firul B: furtună, risc de avarii și echipe trimise din timp

Branch: `Teo-B-furtuna`. Status: `status/Teo-B-furtuna.md`.

## Ce deții

`src/cyberpunks/b_furtuna/`, `tests/b/`, `reports/B/`, `docs/data/B.md`, `docs/research/B.md`, `data/samples/B/`, secțiunea B din `Makefile`, `status/Teo-B-furtuna.md`.

## De ce contează pentru PPC

- Reziliența rețelei e o problemă spusă public de PPC (Daniel Albu, șeful echipei de date și infrastructură, How to Web 2026). Indicatorii de întrerupere ai Rețele Electrice în S1 2026: SAIDI 35 de minute, SAIFI 0,90. Rețeaua are circa 136.000 km de linii. Din noiembrie 2025 au un sistem nou de gestionare a echipelor de teren (WFM).
- PDF-ul temei: "ce alarmă e reală, ce echipamente riscă să se defecteze", "regresie și prognoză pe serii de timp", "date externe: prognoze și istoric meteo".

## Faza 0: cercetare (cel mult 45 de minute, subagenți în paralel), scrisă în `docs/research/B.md`

1. EAGLE-I (ORNL): clienți fără curent pe comitat, la 15 minute, 2014-2024. Figshare: https://figshare.com/articles/dataset/The_Environment_for_Analysis_of_Geo-Located_Energy_Information_s_Recorded_Electricity_Outages_2014-2022/24237376 (plus înregistrările ORNL pe ani). Fișierele, mărimile, câmpurile, licența, indicele de calitate (DQI), clienții pe comitat. Alege un subset (state, ani) care se descarcă și se procesează în timp util.
2. Vremea istorică: Open-Meteo archive (fără cheie; rafale, vânt, precipitații, zăpadă, temperatură), cereri pe mai multe coordonate deodată, limitele de utilizare. Opțional NOAA Storm Events (tipurile de evenimente).
3. O zi REALĂ din România cu furtuni, ideal vara, cu soare puternic dimineața (ca firul C să aibă lucru în aceeași zi), cu întreruperi raportate în presă în Muntenia Sud, Dobrogea sau Banat. Alege data până la ora 15:00 și scrie-o în status, la "Cereri către orchestrator". Devine data scenariului `demo-vara` pentru toate firele. Notează articolele de presă cu cifre (clienți fără curent, localități) pentru validarea calitativă.
4. Ce raportează literatura despre predicția întreruperilor din vreme (repere de performanță).

## Ce construiești

- Date: EAGLE-I plus vremea istorică Open-Meteo pe centroizii comitatelor, într-un tabel zonă × zi (sau fereastră de 6 ore). Ținta: procentul maxim de clienți fără curent și probabilitatea unui eveniment semnificativ (prag justificat, de exemplu peste 1% din clienți).
- Baseline-uri: climatologia (rata istorică pe lună și zonă) și o regulă pe rafală (de exemplu peste 70 km/h).
- Model: LightGBM, clasificare cu probabilitate calibrată plus regresie cuantilă (P10, P50, P90) pentru clienții afectați.
- Evaluare: test pe ani nevăzuți (împărțire pe timp) și pe state nevăzute (generalizare spațială). PR-AUC, Brier, pinball loss pentru cuantile, recall pe evenimentele extreme. `uv run python -m cyberpunks.b_furtuna.evaluate` scrie `reports/B/metrics.json` (contractul `ModelReport`) și figurile.
- Analiza erorilor (`reports/B/error_analysis.md`): evenimente rare și extreme, tipuri (vânt, gheață, zăpadă), calitatea datelor (DQI), ce ai încercat.
- Transferul în România, spus cinstit: modelul învață din SUA și îl aplicăm pe județele Rețele Electrice (`config/area.yaml`) cu vremea reală (prognoza pentru `maine`, istoria pentru `demo-vara`). Features normalizate (procente, nu valori absolute). În interfață și în prezentare: "validat pe date externe, de calibrat pe istoricul de avarii Rețele Electrice". Clienții pe județ: aproximare din date publice (de exemplu cele 3,2 mil. de locuri de consum, împărțite după populație), cu sursa.
- Validare calitativă: ce ar fi recomandat modelul în ziua reală aleasă, comparat cu ce a scris presa (în `reports/B/backtest_romania.md`).
- Incertitudine: prognoza ensemble Open-Meteo sau lățimea intervalului cuantilelor. Când intervalul e prea larg: `abstain`, `human_review`, cu motiv.
- Robustețe: vreme lipsă, valori imposibile, zone fără istoric.
- Explicabilitate: SHAP ("rafale de 85 km/h", "32 mm de ploaie în 48 de ore") și zile istorice asemănătoare, cu ce s-a întâmplat atunci.
- Valoare: clienți-oră evitați × cost (`config/economics.yaml`, cheia `storm`). Lucrarea: `preposition_crew`, cu `time_window` înainte de începutul furtunii, `crew_skill` `mv_grid` sau `lv_grid`, `asset_type` `zone`.
- Ieșirea: `uv run python -m cyberpunks.b_furtuna.predict --scenario <s> --date <d>` scrie `outputs/work_items/<s>/B.jsonl` și `outputs/series/<s>/<id>.json` (vântul și riscul pe ore). Funcție importabilă: `cyberpunks.b_furtuna.predict.run(scenario: str, date: str) -> pathlib.Path`.
- Model card: `reports/B/model_card.md`.

## Milestones (ora României)

- 14:30 M0: `docs/research/B.md`, subset ales și descărcarea pornită, status completat.
- 15:00 data reală pentru `demo-vara`, în status.
- 17:30 M1: baseline și primul model, `metrics.json` valid, `B.jsonl` valid pentru `demo-vara` și `maine`.
- 21:30 M2: modelul bate baseline-ul pe test separat, cuantile, calibrare, SHAP.
- 03:00 M3: analiza erorilor, backtest-ul pe ziua din România, teste de robustețe în `tests/b/`.
- 08:00 M4: model card, comenzi reproductibile în `docs/data/B.md`, curățenie.
