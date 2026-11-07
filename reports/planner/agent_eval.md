# Evaluarea agentului: cifrele (generat de script)

Generat automat de `uv run python -m cyberpunks.planner.evaluate --days 30 --seed 7 --meters 120` la 2026-11-07T14:34:22+02:00 (`planner@0.1.0+4f9fcba`). Lume SINTETICĂ, 30 de zile, 120 de lucrări A pe zi. Metoda: `reports/planner/README.md`.

| Strategie | Valoare netă pe zi (lei) | Km pe zi | Vizite fără problemă reală | Urgențe ratate | Furtuni reale acoperite |
|---|---|---|---|---|---|
| Agentul (reguli + OR-Tools) | 35.061 | 352 | 37,3% | 19,6% | 37 din 48 |
| Top-K după scor | 23.255 | 511 | 29,3% | 26,8% | 33 din 48 |
| Primul venit | 23.552 | 515 | 63,3% | 26,8% | 40 din 48 |
| Aleator | 18.203 | 481 | 56,7% | 44,6% | 30 din 48 |
| Doar contoare (o singură sursă) | 5.459 | 336 | 22,8% | 85,7% | 0 din 48 |

Agentul aduce cu 49% mai multă valoare netă decât cea mai bună strategie simplă (primul venit).

## Pe surse (vizite fără problemă reală / vizite)

| Strategie | Contoare (A) | Furtună (B) | Tensiune (C) |
|---|---|---|---|
| Agentul (reguli + OR-Tools) | 136 / 371 | 30 / 67 | 15 / 47 |
| Top-K după scor | 94 / 412 | 31 / 64 | 43 / 98 |
| Primul venit | 286 / 422 | 36 / 76 | 38 / 71 |
| Aleator | 248 / 426 | 30 / 60 | 55 / 101 |
| Doar contoare (o singură sursă) | 94 / 412 | 0 / 0 | 0 / 0 |

Agentul a mai trimis 1406 citiri la distanță (din care 746 pe probleme reale) și 46 cazuri la om (din care 22 reale). În evaluare ele nu primesc valoare în ziua respectivă, doar costul.

## Robustețe: model supra-încrezător (10 zile, adevărul ~ Bernoulli(scor^1.6))

| Strategie | Valoare netă pe zi (lei) | Urgențe ratate |
|---|---|---|
| Agentul (reguli + OR-Tools) | 19.181 | 18,2% |
| Top-K după scor | 14.011 | 18,2% |
| Primul venit | 9.044 | 27,3% |
| Aleator | 6.298 | 45,5% |
| Doar contoare (o singură sursă) | 3.111 | 90,9% |

## Ablații: ce aduce fiecare piesă (aceleași zile)

| Varianta | Valoare netă pe zi (lei) | Km pe zi | Vizite fără problemă reală |
|---|---|---|---|
| Agentul complet | 35.061 | 352 | 37,3% |
| Fără pragul etic (vizită și sub scorul 0,5, dacă merită) | 40.806 | 381 | 44,6% |
| Aceleași reguli, trasee făcute greedy în loc de OR-Tools | 34.384 | 391 | 37,1% |

## Ziua demo (2025-07-08): lucrările reale ale modelului A, cu adevărul injectat

391 lucrări A, din care 274 probleme reale (valoare reală 186.012 lei). Valoarea capturată e valoarea reală a problemei, nu estimarea modelului. Adevărul vine de la firul A (`A_ground_truth.csv`).

| Strategie | Valoare netă (lei) | Vizite | Probleme reale găsite | Vizite fără problemă | Cazuri reale de siguranță vizitate | Km |
|---|---|---|---|---|---|---|
| Agentul (reguli + OR-Tools) | 2.529 | 33 | 33 | 0 | 29 din 50 | 180 |
| Agentul fără siguranța obligatorie (ablație) | 25.394 | 29 | 29 | 0 | 14 din 50 | 130 |
| Top-K după scor | 6.179 | 24 | 24 | 0 | 2 din 50 | 218 |
| Primul venit | 28.825 | 23 | 23 | 0 | 2 din 50 | 176 |
| Aleator | 986 | 27 | 15 | 12 | 5 din 50 | 265 |

Agentul a trimis în plus 292 citiri la distanță (din care 224 pe probleme reale) și 25 cazuri la om (din care 9 reale). „Primul venit” urmează aici ordinea din fișierul modelului A, care e deja clasamentul lui după valoare. Agentul trimite întâi toate cazurile cu risc pentru oameni (regula R-SAFETY), chiar dacă valorează puțin în lei; ablația arată cât costă regula și câte cazuri de siguranță ar rămâne nevizitate fără ea.

## Sensibilitate la ipotezele fără sursă

| Parametru | Valoare | Agentul (lei/zi) | Top-K (lei/zi) | Avantajul agentului |
|---|---|---|---|---|
| `cost_per_customer_hour_lei` | 5,5 | 17.575 | 9.916 | +77,2% |
| `cost_per_customer_hour_lei` | 15,0 | 43.548 | 29.412 | +48,1% |
| `preposition_cost_lei_per_crew_shift` | 1.500,0 | 38.280 | 25.815 | +48,3% |
| `preposition_cost_lei_per_crew_shift` | 4.100,0 | 31.824 | 20.268 | +57,0% |
| `inspection_visit_cost_lei` | 180,0 | 36.162 | 24.216 | +49,3% |
| `inspection_visit_cost_lei` | 340,0 | 33.966 | 22.019 | +54,3% |
