# Analiza erorilor, modelul B (risc de avarii la furtună)

Generat de `uv run python -m cyberpunks.b_furtuna.error_analysis`. Model `b-lgbm@409ba59`, antrenat pe 2023-2024, evaluat pe 2025 (6.935 zile-comitat, 736 evenimente). Pragul de decizie: 0.16.

## Pe tipuri de vreme

| tip | zile | evenimente | prevalență | PR-AUC | recall la prag | alarme false / 100 zile calme | P medie pe evenimente |
|---|---|---|---|---|---|---|---|
| fără semnal meteo puternic | 5328 | 448 | 0.084 | 0.154 | 0.205 | 7.7 | 0.115 |
| ploaie abundentă (≥ 30 mm în 48 h) | 154 | 32 | 0.208 | 0.37 | 0.781 | 53.3 | 0.248 |
| ploaie la sub 0 °C (polei, chiciură) | 141 | 22 | 0.156 | 0.239 | 0.318 | 11.8 | 0.124 |
| vânt (rafale ≥ 60 km/h) | 1125 | 221 | 0.196 | 0.378 | 0.67 | 38.3 | 0.276 |
| zăpadă (≥ 5 cm în 3 zile) | 187 | 13 | 0.07 | 0.103 | 0.231 | 7.5 | 0.099 |

## Pe sezoane

| sezon | zile | evenimente | prevalență | PR-AUC | recall la prag | alarme false / 100 zile calme | P medie pe evenimente |
|---|---|---|---|---|---|---|---|
| iarna | 1710 | 151 | 0.088 | 0.241 | 0.344 | 9.8 | 0.178 |
| primăvara | 1748 | 240 | 0.137 | 0.317 | 0.467 | 16.9 | 0.202 |
| toamna | 1729 | 138 | 0.08 | 0.146 | 0.188 | 7.1 | 0.115 |
| vara | 1748 | 207 | 0.118 | 0.217 | 0.411 | 19.0 | 0.16 |

## Pe mărimea comitatului

| mărime | zile | evenimente | prevalență | PR-AUC | recall la prag | alarme false / 100 zile calme | P medie pe evenimente |
|---|---|---|---|---|---|---|---|
| comitate mici | 2555 | 235 | 0.092 | 0.232 | 0.404 | 12.4 | 0.172 |
| comitate medii | 2190 | 273 | 0.125 | 0.255 | 0.377 | 14.2 | 0.167 |
| comitate mari | 2190 | 228 | 0.104 | 0.234 | 0.338 | 12.9 | 0.167 |

## Evenimente extreme (vârf ≥ 10% din clienți)

67 evenimente extreme în 2025; modelul le prinde la prag pe 36 (54%). P medie: 0.25.

Cele mai mari ratate (P sub prag):

| county | state | date | pct_out_max | p | gust_max | gust_prev | precip_48h | snow_3d | ice_proxy |
|---|---|---|---|---|---|---|---|---|---|
| Anderson County | KY | 2025-11-12 | 0.632 | 0.071 | 48.6 | 50.4 | 0.0 | 1.12 | 0.0 |
| Clinton County | IL | 2025-02-02 | 0.402 | 0.055 | 31.0 | 40.0 | 0.0 | 0.0 | 0.0 |
| Anderson County | KY | 2025-07-10 | 0.382 | 0.126 | 25.9 | 28.1 | 14.9 | 0.0 | 0.0 |
| Clinton County | IL | 2025-03-15 | 0.249 | 0.13 | 63.7 | 90.4 | 4.1 | 0.0 | 0.0 |
| Crawford County | IL | 2025-03-23 | 0.24 | 0.13 | 52.2 | 41.4 | 16.6 | 0.0 | 0.0 |
| Coles County | IL | 2025-03-30 | 0.222 | 0.092 | 64.4 | 45.0 | 13.3 | 0.0 | 0.0 |
| Anderson County | KY | 2025-07-25 | 0.213 | 0.111 | 25.9 | 32.4 | 0.30000000000000004 | 0.0 | 0.0 |
| Cass County | MO | 2025-08-19 | 0.203 | 0.111 | 30.2 | 32.4 | 3.9 | 0.0 | 0.0 |
| Ingham County | MI | 2025-05-16 | 0.191 | 0.055 | 48.6 | 46.8 | 3.6 | 0.0 | 0.0 |
| Bullitt County | KY | 2025-11-12 | 0.185 | 0.073 | 42.8 | 46.4 | 0.0 | 0.5600000000000005 | 0.0 |

## Cele mai sigure alarme false

| county | state | date | pct_out_max | p | gust_max | precip_48h | snow_3d |
|---|---|---|---|---|---|---|---|
| Anderson County | KY | 2025-02-16 | 0.001 | 1.0 | 75.2 | 86.2 | 5.53 |
| Ashtabula County | OH | 2025-04-02 | 0.0007 | 0.8 | 82.1 | 22.7 | 0.0 |
| Chautauqua County | NY | 2025-04-03 | 0.0026 | 0.8 | 84.2 | 28.7 | 0.21000000000000088 |
| Cass County | MO | 2025-04-02 | 0.0069 | 0.8 | 78.1 | 15.4 | 0.0 |
| Bullitt County | KY | 2025-04-02 | 0.0072 | 0.779 | 85.7 | 2.7 | 0.0 |
| Essex County | NY | 2025-02-07 | 0.0 | 0.62 | 105.5 | 8.8 | 5.1099999999999985 |
| Ashtabula County | OH | 2025-12-20 | 0.0028 | 0.62 | 78.1 | 15.2 | 3.1500000000000035 |
| Essex County | NY | 2025-06-20 | 0.0096 | 0.62 | 101.5 | 6.6 | 0.0 |
| Cass County | MO | 2025-03-04 | 0.0022 | 0.62 | 68.4 | 37.4 | 1.54 |
| Essex County | NY | 2025-02-14 | 0.0034 | 0.62 | 84.2 | 17.5 | 13.51 |

## Cuantilele (cât de mare, dacă se întâmplă)

Pe zilele cu eveniment din 2025: vârful real e în intervalul P10-P90 în 62% din cazuri (ținta: 80%), peste P90 în 18%, sub P10 în 21%.

## Calitatea datelor

- Comitat-ani scoși pentru acoperire EAGLE-I sub 50% din zile: 0.
- Zile scoase pentru valori blocate (același vârf ≥ 0,5% din clienți 4 zile la rând): 0.
- Vârfuri peste numărul de clienți (MCC e modelat), tăiate la 100%: 0.
- Rânduri cu vreme lipsă: 0. Probleme de vreme: niciuna.
- În EAGLE-I, lipsa unui rând înseamnă fie zero clienți afectați, fie o pauză în colectare (Brelsford et al. 2024). Le tratăm ca zero doar în comitatele cu acoperire bună, așa că o parte din „alarmele false” pot fi avarii nevăzute.

## Ce am încercat

| varianta | ce | pr_auc | brier | prevalence |
|---|---|---|---|---|
| baza | features-urile din features.py, constrângeri monotone | 0.2467 | 0.0902 | 0.1083 |
| fara_monotonie | fără constrângeri monotone | 0.2481 | 0.0898 | 0.1083 |
| fara_intarzieri | fără vremea din zilele precedente | 0.2451 | 0.0903 | 0.1083 |
| doar_vreme | fără mărimea și densitatea zonei | 0.2333 | 0.0906 | 0.1083 |
| clima_locala | + rafala față de clima comitatului (medie, p95 pe anii de antrenare) | 0.2431 | 0.0899 | 0.1083 |
| ploaie_extra | + intensitatea ploii și ploaia pe 30 de zile | 0.2462 | 0.0899 | 0.1083 |
| prag_2pct | evenimentul la ≥ 2% din clienți (în loc de 1%) | 0.1664 | 0.0578 | 0.0643 |
| prag_5pct | evenimentul la ≥ 5% din clienți | 0.0691 | 0.023 | 0.0237 |
| arbori_mai_mari | num_leaves 31, min_data_in_leaf 20 | 0.2346 | 0.0905 | 0.1083 |

