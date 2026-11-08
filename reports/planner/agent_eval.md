# Evaluarea agentului: cifrele (generat de script)

Generat automat de `uv run python -m cyberpunks.planner.evaluate --days 30 --seed 7 --meters 120` la 2026-11-08T08:03:51+02:00 (`planner@0.1.0+7675c21`). Lume SINTETICĂ, 30 de zile, 120 de lucrări A pe zi. Metoda: `reports/planner/README.md`.

| Strategie | Valoare netă pe zi (lei) | Km pe zi | Vizite fără problemă reală | Urgențe ratate | Furtuni reale acoperite |
|---|---|---|---|---|---|
| Agentul (reguli + OR-Tools) | 35.060 | 350 | 37,4% | 25,0% | 37 din 48 |
| Top-K după scor | 23.255 | 511 | 29,3% | 26,8% | 33 din 48 |
| Primul venit | 23.552 | 515 | 63,3% | 26,8% | 40 din 48 |
| Aleator | 18.203 | 481 | 56,7% | 44,6% | 30 din 48 |
| Doar contoare (o singură sursă) | 5.459 | 336 | 22,8% | 85,7% | 0 din 48 |

Agentul aduce cu 49% mai multă valoare netă decât cea mai bună strategie simplă (primul venit).

## Pe surse (vizite fără problemă reală / vizite)

| Strategie | Contoare (A) | Furtună (B) | Tensiune (C) |
|---|---|---|---|
| Agentul (reguli + OR-Tools) | 135 / 367 | 30 / 67 | 15 / 47 |
| Top-K după scor | 94 / 412 | 31 / 64 | 43 / 98 |
| Primul venit | 286 / 422 | 36 / 76 | 38 / 71 |
| Aleator | 248 / 426 | 30 / 60 | 55 / 101 |
| Doar contoare (o singură sursă) | 94 / 412 | 0 / 0 | 0 / 0 |

Agentul a mai trimis 1410 citiri la distanță (din care 749 pe probleme reale) și 46 cazuri la om (din care 22 reale). În evaluare ele nu primesc valoare în ziua respectivă, doar costul.

## Robustețe: model supra-încrezător (10 zile, adevărul ~ Bernoulli(scor^1.6))

| Strategie | Valoare netă pe zi (lei) | Urgențe ratate |
|---|---|---|
| Agentul (reguli + OR-Tools) | 19.449 | 18,2% |
| Top-K după scor | 14.011 | 18,2% |
| Primul venit | 9.044 | 27,3% |
| Aleator | 6.298 | 45,5% |
| Doar contoare (o singură sursă) | 3.111 | 90,9% |

## Ablații: ce aduce fiecare piesă (aceleași zile)

| Varianta | Valoare netă pe zi (lei) | Km pe zi | Vizite fără problemă reală |
|---|---|---|---|
| Agentul complet | 35.060 | 350 | 37,4% |
| Fără pragul etic (vizită și sub scorul 0,5, dacă merită) | 40.886 | 381 | 44,3% |
| Aceleași reguli, trasee făcute greedy în loc de OR-Tools | 34.429 | 391 | 37,1% |

## Ziua demo (2025-07-08): lucrările reale ale modelului A, cu adevărul injectat

532 lucrări A, din care 404 probleme reale (valoare reală 205.555 lei). Valoarea capturată e valoarea reală a problemei, nu estimarea modelului. Adevărul vine de la firul A (`A_ground_truth.csv`).

| Strategie | Valoare netă (lei) | Vizite | Probleme reale găsite | Vizite fără problemă | Cazuri reale de siguranță vizitate | Km |
|---|---|---|---|---|---|---|
| Agentul (reguli + OR-Tools) | 17.487 | 23 | 23 | 0 | 13 din 40 | 178 |
| Agentul fără siguranța obligatorie (ablație) | 27.206 | 25 | 25 | 0 | 5 din 40 | 129 |
| Top-K după scor | 4.208 | 22 | 22 | 0 | 0 din 40 | 249 |
| Primul venit | 29.335 | 24 | 24 | 0 | 0 din 40 | 172 |
| Aleator | 1.871 | 27 | 23 | 4 | 2 din 40 | 228 |

Agentul a trimis în plus 389 citiri la distanță (din care 301 pe probleme reale) și 13 cazuri la om (din care 5 reale). „Primul venit” urmează aici ordinea din fișierul modelului A, care e deja clasamentul lui după valoare. Agentul trimite întâi toate cazurile cu risc pentru oameni (regula R-SAFETY), chiar dacă valorează puțin în lei; ablația arată cât costă regula și câte cazuri de siguranță ar rămâne nevizitate fără ea.

## Sensibilitate la ipotezele fără sursă

| Parametru | Valoare | Agentul (lei/zi) | Top-K (lei/zi) | Avantajul agentului |
|---|---|---|---|---|
| `cost_per_customer_hour_lei` | 5,5 | 17.575 | 9.916 | +77,2% |
| `cost_per_customer_hour_lei` | 15,0 | 43.547 | 29.412 | +48,1% |
| `preposition_cost_lei_per_crew_shift` | 1.500,0 | 38.278 | 25.815 | +48,3% |
| `preposition_cost_lei_per_crew_shift` | 4.100,0 | 31.823 | 20.268 | +57,0% |
| `inspection_visit_cost_lei` | 180,0 | 36.219 | 24.216 | +49,6% |
| `inspection_visit_cost_lei` | 340,0 | 34.011 | 22.019 | +54,5% |
