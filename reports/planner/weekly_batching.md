# Tura de zonă de vineri față de plecarea a doua zi

Lume **sintetică**: 4 săptămâni din 2026-11-02, 40 contoare semnalate pe zi în București-Ilfov, seed 11. Aceleași lucrări, reguli, echipe și solver pentru ambele politici. Comanda: `uv run python -m cyberpunks.planner.batching_benchmark`.

| | a doua zi | tura de zonă |
|---|---:|---:|
| Vizite făcute | 116 | 116 |
| Zile-echipă pe teren | 34 | 28 |
| Opriri pe zi-echipă | 3.41 | 4.14 |
| Kilometri | 2402.8 | 1891.0 |
| Km pe vizită | 20.71 | 16.3 |
| Costul drumului | 12862.98 lei | 11067.3 lei |
| Costul drumului pe vizită | 110.89 lei | 95.41 lei |
| Costul așteptării (pierdere) | 2006.53 lei | 3997.11 lei |
| Așteptare medie (zile lucrătoare) | 1.0 | 3.1 |
| Așteptare maximă (zile lucrătoare) | 1 | 9 |
| Depășiri de termen | 0 | 0 |
| Rămase la final | 0 | 0 |

**Economie:** 511.8 km (21.3%), 1795.68 lei pe drum și 6 zile-echipă (5702.4 lei, la 950 lei pe zi-echipă). Așteptarea costă în plus 1990.58 lei (energie pierdută până la vizită). **Net: 5507.5 lei.**

Zilele-echipă eliberate nu sunt bani plătiți mai puțin: echipele fac în acele zile alte lucrări (avarii, branșamente). Le socotim la costul unei zile de muncă, ca valoare a timpului eliberat.
