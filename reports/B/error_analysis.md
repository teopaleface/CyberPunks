# Analiza erorilor, modelul B (risc de avarii la furtună)

Generat de `uv run python -m cyberpunks.b_furtuna.error_analysis`. Model `b-lgbm@c5c8344`, antrenat pe 2023-2024, evaluat pe 2025 (29.200 zile-comitat, 3.014 evenimente). Pragul de decizie: 0.16.

## Pe tipuri de vreme

| tip | zile | evenimente | prevalență | PR-AUC | recall la prag | alarme false / 100 zile calme | P medie pe evenimente |
|---|---|---|---|---|---|---|---|
| fără semnal meteo puternic | 22689 | 1844 | 0.081 | 0.169 | 0.239 | 6.9 | 0.122 |
| ploaie abundentă (≥ 30 mm în 48 h) | 710 | 156 | 0.22 | 0.394 | 0.808 | 61.7 | 0.28 |
| ploaie la sub 0 °C (polei, chiciură) | 617 | 94 | 0.152 | 0.312 | 0.426 | 13.8 | 0.164 |
| vânt (rafale ≥ 60 km/h) | 4419 | 854 | 0.193 | 0.447 | 0.726 | 35.9 | 0.33 |
| zăpadă (≥ 5 cm în 3 zile) | 765 | 66 | 0.086 | 0.121 | 0.121 | 5.7 | 0.094 |

## Pe sezoane

| sezon | zile | evenimente | prevalență | PR-AUC | recall la prag | alarme false / 100 zile calme | P medie pe evenimente |
|---|---|---|---|---|---|---|---|
| iarna | 7200 | 604 | 0.084 | 0.303 | 0.391 | 7.9 | 0.214 |
| primăvara | 7360 | 996 | 0.135 | 0.348 | 0.503 | 16.5 | 0.224 |
| toamna | 7280 | 562 | 0.077 | 0.167 | 0.215 | 6.7 | 0.124 |
| vara | 7360 | 852 | 0.116 | 0.234 | 0.441 | 17.6 | 0.175 |

## Pe mărimea comitatului

| mărime | zile | evenimente | prevalență | PR-AUC | recall la prag | alarme false / 100 zile calme | P medie pe evenimente |
|---|---|---|---|---|---|---|---|
| comitate mici | 9855 | 1206 | 0.122 | 0.302 | 0.459 | 15.3 | 0.203 |
| comitate medii | 9855 | 1111 | 0.113 | 0.29 | 0.437 | 13.7 | 0.197 |
| comitate mari | 9490 | 697 | 0.073 | 0.215 | 0.278 | 7.4 | 0.155 |

## Evenimente extreme (vârf ≥ 10% din clienți)

264 evenimente extreme în 2025; modelul le prinde la prag pe 143 (54%). P medie: 0.24.

Cele mai mari ratate (P sub prag):

| county | state | date | pct_out_max | p | gust_max | gust_prev | precip_48h | snow_3d | ice_proxy |
|---|---|---|---|---|---|---|---|---|---|
| Nassau County | NY | 2025-02-02 | 1.0 | 0.009 | 33.5 | 57.2 | 5.7 | 1.33 | 0.6 |
| Otsego County | MI | 2025-04-01 | 0.908 | 0.102 | 37.1 | 52.6 | 1.7 | 0.5600000000000009 | 0.0 |
| Otsego County | MI | 2025-04-04 | 0.715 | 0.157 | 26.3 | 76.7 | 1.1 | 2.5900000000000007 | 0.0 |
| Anderson County | KY | 2025-11-12 | 0.632 | 0.056 | 48.6 | 50.4 | 0.0 | 1.12 | 0.0 |
| Clark County | KY | 2025-11-12 | 0.623 | 0.047 | 52.9 | 52.9 | 0.0 | 0.77 | 0.0 |
| Otsego County | MI | 2025-04-05 | 0.545 | 0.157 | 53.3 | 26.3 | 2.7 | 1.4000000000000008 | 0.7 |
| Hanover County | VA | 2025-07-27 | 0.532 | 0.157 | 22.0 | 21.2 | 16.6 | 0.0 | 0.0 |
| Grayson County | KY | 2025-01-21 | 0.514 | 0.072 | 35.6 | 38.5 | 0.0 | 1.54 | 0.0 |
| Henderson County | KY | 2025-01-06 | 0.5 | 0.157 | 47.5 | 59.0 | 28.299999999999997 | 6.6499999999999995 | 0.3 |
| Cambria County | PA | 2025-04-29 | 0.451 | 0.1 | 60.1 | 33.5 | 1.2 | 0.0 | 0.0 |

## Cele mai sigure alarme false

| county | state | date | pct_out_max | p | gust_max | precip_48h | snow_3d |
|---|---|---|---|---|---|---|---|
| Essex County | NY | 2025-02-17 | 0.0012 | 0.957 | 98.3 | 32.1 | 25.970000000000002 |
| Essex County | NY | 2025-01-02 | 0.0043 | 0.957 | 99.0 | 18.3 | 12.879999999999997 |
| Van Buren County | MI | 2025-12-30 | 0.0047 | 0.957 | 69.1 | 12.8 | 8.679999999999998 |
| Van Buren County | MI | 2025-11-27 | 0.0018 | 0.909 | 95.4 | 12.0 | 7.069999999999998 |
| Clark County | KY | 2025-02-16 | 0.0044 | 0.905 | 88.6 | 71.6 | 3.57 |
| Chautauqua County | NY | 2025-04-03 | 0.0026 | 0.875 | 84.2 | 28.7 | 0.21000000000000088 |
| Newport News city | VA | 2025-03-05 | 0.0093 | 0.875 | 105.5 | 17.8 | 0.0 |
| Newport News city | VA | 2025-03-06 | 0.0001 | 0.849 | 69.1 | 17.900000000000002 | 0.0 |
| Lincoln County | KY | 2025-02-16 | 0.0012 | 0.849 | 81.4 | 94.5 | 3.08 |
| Ohio County | KY | 2025-04-04 | 0.0025 | 0.849 | 51.1 | 101.6 | 0.0 |

## Verificare pe evenimente cunoscute

Zilele din anii de antrenare arată doar că datele sunt citite corect (ora, ziua, vremea). Nu sunt o evaluare: modelul le-a văzut.

| eveniment | comitat | ziua | vârf | rafală | ploaie 48 h | ploaie la sub 0 °C | zăpadă 3 zile | P model |
|---|---|---|---|---|---|---|---|---|
| Furtuna de iarnă din februarie 2023, cu gheață: cel puțin 811.000 de întreruperi în Michigan (https://en.wikipedia.org/wiki/February_2023_North_American_winter_storm) | Jackson County, MI | 2023-02-22 | 45% | 52 | 29.9 | 28.9 | 0.7 | an de antrenare |
| Valul de tornade din 31 martie - 1 aprilie 2023 (https://en.wikipedia.org/wiki/Tornado_outbreak_of_March_31_%E2%80%93_April_1,_2023) | Crawford County, IL | 2023-03-31 | 84% | 87 | 29.4 | 0.0 | 0.0 | an de antrenare |
| Resturile uraganului Helene (https://en.wikipedia.org/wiki/Hurricane_Helene) | Anderson County, KY | 2024-09-27 | 51% | 81 | 73.7 | 0.0 | 0.0 | an de antrenare |
| Furtuna de zăpadă din martie 2023 (nor'easter) (https://en.wikipedia.org/wiki/2022%E2%80%9323_North_American_winter) | Essex County, NY | 2023-03-14 | 62% | 81 | 44.2 | 0.0 | 30.9 | an de antrenare |
| Posibil artefact de date: două comitate vecine (Anderson și Clark, KY) peste 60%, fără vânt sau ploaie semnificative | Anderson County, KY | 2025-11-12 | 63% | 49 | 0.0 | 0.0 | 1.1 | 0.06 |

## Cuantilele (cât de mare, dacă se întâmplă)

Pe zilele cu eveniment din 2025: vârful real e în intervalul P10-P90 în 81% din cazuri (ținta: 80%), peste P90 în 12%, sub P10 în 7%.

## Calitatea datelor

- Comitat-ani scoși pentru acoperire EAGLE-I sub 50% din zile: 0.
- Zile scoase pentru valori blocate (același vârf ≥ 0,5% din clienți 4 zile la rând): 0.
- Vârfuri peste numărul de clienți (MCC e modelat), tăiate la 100%: 2.
- Rânduri cu vreme lipsă: 0. Probleme de vreme: niciuna.
- În EAGLE-I, lipsa unui rând înseamnă fie zero clienți afectați, fie o pauză în colectare (Brelsford et al. 2024). Le tratăm ca zero doar în comitatele cu acoperire bună, așa că o parte din „alarmele false” pot fi avarii nevăzute.

## Concluzii (calculate din tabelele de mai sus)

- 61% din evenimente apar în zile fără semnal meteo puternic (defecte obișnuite). Vremea nu le poate prezice, iar ele dau plafonul de PR-AUC pe toate zilele.
- Cel mai bine merge la „vânt (rafale ≥ 60 km/h)” (PR-AUC 0.45, recall la prag 73%); cel mai slab la „zăpadă (≥ 5 cm în 3 zile)” (PR-AUC 0.12, recall 12%). Ninsoarea zilnică nu spune dacă zăpada e grea și udă, adică felul care rupe liniile.
- Evenimentele extreme (≥ 10%): 54% prinse la prag. Din cele 121 ratate, 85% au rafale sub 60 km/h în arhivă, iar 74% nu au niciun semnal meteo puternic: fie vijelii locale pe care modelul meteo nu le vede, fie cauze fără legătură cu vremea (defecte, artefacte de date). Nu le putem deosebi fără istoricul de intervenții.
- Cuantilele: 81% din vârfurile reale în intervalul P10-P90, după calibrarea conformală.

## Ce am încercat

| varianta | ce | pr_auc | brier | prevalence |
|---|---|---|---|---|
| baza | modelul livrat: vânt, ploaie, zăpadă, polei, sezon, mărimea zonei; constrângeri monotone | 0.2777 | 0.0841 | 0.1032 |
| fara_monotonie | fără constrângeri monotone | 0.2738 | 0.0843 | 0.1032 |
| fara_intarzieri | fără vremea din zilele precedente | 0.273 | 0.0844 | 0.1032 |
| doar_vreme | fără mărimea și densitatea zonei | 0.2342 | 0.0867 | 0.1032 |
| clima_locala | + rafala față de clima comitatului (medie, p95 pe anii de antrenare) | 0.2762 | 0.0841 | 0.1032 |
| ploaie_extra | + intensitatea ploii și ploaia pe 30 de zile | 0.2754 | 0.0843 | 0.1032 |
| prag_2pct | evenimentul la ≥ 2% din clienți (în loc de 1%) | 0.1968 | 0.0526 | 0.0601 |
| prag_5pct | evenimentul la ≥ 5% din clienți | 0.1004 | 0.0212 | 0.0222 |
| arbori_mai_mari | num_leaves 31, min_data_in_leaf 20 | 0.2746 | 0.0842 | 0.1032 |
| coada_rafalei | + cât trece rafala peste 60 km/h | 0.2763 | 0.0842 | 0.1032 |
| cu_temperaturi | + temperaturile și radiația (scoase din model: trimiteau echipe la caniculă în România) | 0.2829 | 0.0837 | 0.1032 |
| mai_putine_variabile | fără orele de ploaie, vântul mediu și sezonul (cos) | 0.2689 | 0.0847 | 0.1032 |

