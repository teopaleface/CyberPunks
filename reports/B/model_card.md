# Model card: B, riscul de avarii la furtună

Generat de `uv run python -m cyberpunks.b_furtuna.model_card` din `reports/B/metrics.json` și `reports/B/metrics_detail.json`. Versiunea modelului: `b-lgbm@c5c8344`, creat la 2026-11-07T14:59:07+02:00.

## Ce face

Estimează, pentru fiecare zonă din aria Rețele Electrice și pentru ziua de mâine, probabilitatea ca peste 1% din clienții zonei să rămână fără curent în același timp, plus câți clienți ar fi afectați dacă se întâmplă (P10/P50/P90). Agentul folosește estimarea ca să trimită echipe din timp (`preposition_crew`) sau, când nu e sigur, să lase decizia dispecerului (`human_review`).


## De ce contează pentru PPC

- Întreruperile și compensațiile automate sunt pe lista problemelor neacoperite de cele 9 proiecte AI ale PPC (`memory/12-probleme-reale-ppc-2026.md`, problema D1).
- Rețele Electrice plătește circa 85% din compensațiile automate naționale (raportul ANRE pe 2024).
- Standardul ANRE (Ord. 46/2021, art. 15) cere restabilirea în 4/6/12 h pe vreme normală și în 48/72 h pe vreme deosebită; la depășire, fiecare client JT primește automat 30 lei. O echipă aflată deja în zonă scurtează restabilirea exact în zilele în care rețeaua e cea mai solicitată.
- PPC are din noiembrie 2025 un sistem nou de gestionare a echipelor de teren (WFM). Modelul îi dă ce-i lipsește: unde și când vor fi avarii mâine, cu cât de sigur e.

- **Utilizatori:** dispecerii Rețele Electrice, prin planificator și interfață.
- **Nu e pentru:** decizii automate fără om, despăgubiri, evaluarea clienților. Nu folosește date personale.

## Date

- **Ținta:** EAGLE-I (ORNL), clienți fără curent pe comitat la 15 minute, CC BY 4.0, https://doi.org/10.6084/m9.figshare.24237376.v4.
- **Eșantion:** 80 comitate din 8 state SUA (IL, KY, MI, MO, NY, OH, PA, VA), ani de antrenare 2023, 2024, cu 58.480 zile-comitat și 5.595 de evenimente.
- **Vremea:** Open-Meteo Historical Weather API (best_match: ERA5, ERA5-Land, ECMWF IFS), 10 variabile zilnice pe centroidul comitatului. Aceeași sursă e folosită în România (arhiva pentru zile trecute, prognoza pentru mâine).
- **Curățare:** acoperire EAGLE-I sub 50% din zile pe comitat-an, valori blocate, vârfuri peste numărul de clienți, valori meteo imposibile. Detalii în `docs/data/B.md`.
- **Ce a scos curățarea:** 0 comitat-ani cu acoperire slabă, 0 zile cu valori blocate, 2 vârfuri tăiate la 100%.
- **Date sintetice:** niciuna în antrenare și în test (`synthetic_share` = 0.0).

## Modelul

- **Pasul 1:** LightGBM pentru P(vârf ≥ 1% din clienți), cu constrângeri monotone pe vânt, ploaie, zăpadă și polei (riscul nu scade când vremea se înrăutățește). Calibrare izotonică pe scoruri out-of-fold, cu fold-uri pe săptămâni.
- **Pasul 2:** LightGBM quantile (P10, P50, P90) pentru vârful procentual în zilele cu eveniment. Intervalul e lărgit prin calibrare conformală (CQR), cu 0,060 pe scara log.
- **Features:** `gust_max`, `wind_max`, `gust_prev`, `gust_max_2d`, `precip`, `precip_48h`, `precip_7d`, `precip_hours`, `snow`, `snow_3d`, `ice_proxy`, `doy_sin`, `doy_cos`, `log_customers`, `log_density`.
- **Pragul de decizie:** 0,16, cel mai bun F1 pe scorurile out-of-fold din anii de antrenare. Planificatorul decide final, după valoare și echipele disponibile.

## Evaluare (test separat)

Testul: pe timp: antrenare 2023-2024, test 2025 (an nevăzut), 80 comitate din 8 state SUA; plus state nevăzute (leave-one-state-out) în reports/B/metrics_detail.json. 29.200 zile-comitat; prevalența evenimentului e 10,3%.

| Metrică | Model | Climatologie comitat × lună | Climatologie pe lună | Regula pe rafală |
|---|---|---|---|---|
| PR-AUC (principala) | **0,278** | 0,151 | 0,120 | 0,182 |
| ROC-AUC | 0,725 | 0,612 | 0,552 | 0,611 |
| Brier (mai mic e mai bine) | 0,0841 | 0,0914 | 0,0924 | 0,0890 |
| Recall evenimente severe (≥ 5%) la prag | 49,8% | 39,9% | 52,7% | 42,7% |
| Recall evenimente extreme (≥ 10%) la prag | 54,2% | 41,7% | 54,2% | 45,8% |

- **Cuantile** (zilele cu eveniment din test): acoperirea P10-P90 e 80,8% (ținta 80%; fără calibrarea conformală: 72,2%). Pierderea pinball medie (scara log): model 0,151, climatologia pe lună 0,153.
- **State nevăzute** (leave-one-state-out, 8 state, anul 2025): PR-AUC mediu 0,259, față de climatologia pe lună 0,122 și regula pe rafală 0,188. Modelul bate climatologia în 8 din 8 state. E situația din România: zone fără istoric de avarii.
- **Echipe puține** (8 echipe pe zi pentru 80 zone, câte una în zonele cu scorul cel mai mare): acoperă din clienții afectați 16,7% cu modelul, 14,6% cu regula pe rafală, 12,3% cu climatologia, 7,6% la întâmplare și 88,5% cu un oracol care știe viitorul.
- **Figuri:** `fig_pr_curves.png`, `fig_reliability.png`, `fig_shap_importance.png`; analiza erorilor în `error_analysis.md`; backtestul din România în `backtest_romania.md`.

## Ce am încercat

| Varianta | Ce | PR-AUC | Brier |
|---|---|---|---|
| baza | modelul livrat: vânt, ploaie, zăpadă, polei, sezon, mărimea zonei; constrângeri monotone | 0,278 | 0,0841 |
| fara_monotonie | fără constrângeri monotone | 0,274 | 0,0843 |
| fara_intarzieri | fără vremea din zilele precedente | 0,273 | 0,0844 |
| doar_vreme | fără mărimea și densitatea zonei | 0,234 | 0,0867 |
| clima_locala | + rafala față de clima comitatului (medie, p95 pe anii de antrenare) | 0,276 | 0,0841 |
| ploaie_extra | + intensitatea ploii și ploaia pe 30 de zile | 0,275 | 0,0843 |
| prag_2pct | evenimentul la ≥ 2% din clienți (în loc de 1%) | 0,197 | 0,0526 |
| prag_5pct | evenimentul la ≥ 5% din clienți | 0,100 | 0,0212 |
| arbori_mai_mari | num_leaves 31, min_data_in_leaf 20 | 0,275 | 0,0842 |
| coada_rafalei | + cât trece rafala peste 60 km/h | 0,276 | 0,0842 |
| cu_temperaturi | + temperaturile și radiația (scoase din model: trimiteau echipe la caniculă în România) | 0,283 | 0,0837 |
| mai_putine_variabile | fără orele de ploaie, vântul mediu și sezonul (cos) | 0,269 | 0,0847 |

## Folosirea în România și limitele, spuse cinstit

- **Transfer:** modelul e învățat în SUA și aplicat pe 26 de zone Rețele Electrice. E validat pe date externe (an nevăzut, state nevăzute) și trebuie calibrat pe istoricul de avarii Rețele Electrice înainte de producție. Fiecare lucrare poartă nota asta.
- **Features normalizate:** procente, densitate și logaritmul clienților, nu valori absolute. Zonele mai mari decât orice comitat din antrenare (Bucureștiul) sunt semnalate și trimise la om.
- **Rafalele convective sunt subestimate** de arhive și de prognoze (pe 8 iulie 2025: 40-70 km/h în arhivă, față de 90-120 km/h măsurați). Modelul învață pe aceeași vreme netezită, deci ordonează bine zonele, dar intensitatea locală rămâne incertă.
- **Căldura contează în model:** în datele din SUA, zilele foarte calde aduc avarii (suprasarcină, furtuni de după-amiază). În România, zilele de caniculă primesc deci un risc moderat chiar fără vânt, iar explicația o spune.
- **Evenimentele fără semnal meteo** (defecte de echipament) sunt circa jumătate din evenimentele de 1% și nu pot fi prezise din vreme. De aici vine plafonul de PR-AUC.
- **Clienții pe zonă** sunt o aproximare din populație. Clienții pe județ sunt oficiali (RER, 31.12.2024).
- **Testul folosește vremea reconstituită** (arhiva Open-Meteo), nu prognoza făcută cu o zi înainte. În exploatare, cu prognoza, performanța va fi ceva mai mică, deci cifrele de test sunt mai degrabă o limită de sus. Incertitudinea prognozei e tratată separat: ensemble (40 de membri ICON-EPS) pentru mâine, trei modele pentru zilele trecute.

## „Nu sunt sigur”: când trimite la om

- lipsesc rafala sau ploaia pentru ziua țintă;
- zona sau vremea iese din intervalul văzut la antrenare (cu o marjă de 10%);
- sursele meteo nu se pun de acord (trei modele de prognoză pentru zilele trecute, 40 de membri ICON-EPS pentru mâine), iar intervalul probabilității trece peste prag;
- dacă Open-Meteo nu răspunde, agentul folosește ultima prognoză salvată și o scrie în lucrare.

## Responsabilitate

- **EU AI Act:** sistemele AI pentru infrastructură critică sunt cu risc ridicat. Omul rămâne în buclă: modelul recomandă, iar planificatorul și dispecerul decid. Fiecare decizie are `prediction_id` și `model_version` în jurnalul de audit.
- **Date:** fără date personale. Datele sunt publice, cu licențe deschise, citate în `docs/data/B.md`.

## Reproducere

```bash
make b-data b-weather b-dataset   # date (EAGLE-I ~4 GB, ~6.300 de apeluri Open-Meteo)
uv run python -m cyberpunks.b_furtuna.evaluate   # metricile din acest card
uv run python -m cyberpunks.b_furtuna.experiments && uv run python -m cyberpunks.b_furtuna.error_analysis
uv run python -m cyberpunks.b_furtuna.backtest && uv run python -m cyberpunks.b_furtuna.model_card
```
