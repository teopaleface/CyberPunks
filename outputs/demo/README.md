# Instantaneul demo

Scenariul `demo-vara`, planul `PLAN-demo-vara-20250708-144945-5d00` pentru 2025-07-08, copiat la 2026-11-07 14:49 cu `uv run python -m cyberpunks.planner.snapshot --scenario demo-vara`.

Sursele lucrărilor: A: model, A_bilant: model, B: model, C: model. Activele (contoare, posturi), echipele și bazele sunt SINTETICE, plasate pe hartă reală; vremea și zilele sunt reale. Nimic nu a fost trimis în afară (notificările sunt `demo_only`).

Structura e aceeași ca în `outputs/`: `plans/<s>/` (plan, jurnal, alerte, notificări, raport, ordine de lucru PDF), `series/<s>/` (graficele lucrărilor), `reports/` (metricile modelelor și evaluarea agentului). API-ul le servește când nu există o rulare locală (`GET /api/health` → `mode: demo`).
