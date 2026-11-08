# Tura de zonă de vineri față de plecarea a doua zi

Lume **sintetică**: 4 săptămâni din 2026-11-02, 40 contoare semnalate pe zi în București-Ilfov, seed 11. Aceleași lucrări, reguli, echipe și solver pentru ambele politici. Comanda: `uv run python -m cyberpunks.planner.batching_benchmark`.

| | a doua zi | tura de zonă |
|---|---:|---:|
| Vizite făcute | 116 | 116 |
| Zile-echipă pe teren | 34 | 26 |
| Opriri pe zi-echipă | 3.41 | 4.46 |
| Kilometri | 2402.8 | 1923.0 |
| Km pe vizită | 20.71 | 16.58 |
| Costul drumului | 12862.98 lei | 10638.18 lei |
| Costul drumului pe vizită | 110.89 lei | 91.71 lei |
| Costul așteptării (pierdere) | 2006.53 lei | 4263.41 lei |
| Așteptare medie (zile lucrătoare) | 1.0 | 3.17 |
| Așteptare maximă (zile lucrătoare) | 1 | 6 |
| Depășiri de termen | 0 | 0 |
| Rămase la final | 0 | 0 |

**Economie:** 479.8 km (20.0%), 2224.8 lei pe drum și 8 zile-echipă (7603.2 lei, la 950 lei pe zi-echipă). Așteptarea costă în plus 2256.88 lei (energie pierdută până la vizită). **Net: 7571.12 lei.**

Zilele-echipă eliberate nu sunt bani plătiți mai puțin: echipele fac în acele zile alte lucrări (avarii, branșamente). Le socotim la costul unei zile de muncă, ca valoare a timpului eliberat.
