# Instantaneul demo

Scenariul `maine`, planul `PLAN-maine-20261108-182027-e324` pentru 2026-11-08, copiat la 2026-11-07 18:23 cu `uv run python -m cyberpunks.planner.snapshot --scenario maine`.

Sursele lucrărilor: A: model, B: model, C: model. Activele (contoare, posturi), echipele și bazele sunt SINTETICE, plasate pe hartă reală; vremea și zilele sunt reale. Nimic nu a fost trimis în afară (notificările sunt `demo_only`).

Structura e aceeași ca în `outputs/`: `plans/<s>/` (plan, jurnal, alerte, notificări, raport, ordine de lucru PDF), `series/<s>/` (graficele lucrărilor), `reports/` (metricile modelelor și evaluarea agentului). API-ul le servește când nu există o rulare locală (`GET /api/health` → `mode: demo`).
