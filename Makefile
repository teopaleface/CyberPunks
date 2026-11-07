# Comenzi comune. Fiecare fir își adaugă ținte doar în secțiunea lui, ca să nu apară conflicte la merge.
.PHONY: setup check test lint fixtures schemas validate-fixtures

setup:            ## instalează mediul Python (uv, Python 3.12)
	uv sync

check: lint test  ## ce rulează orchestratorul înainte de fiecare merge

lint:
	uv run ruff check src tests

test:
	uv run pytest

fixtures:         ## regenerează exemplele din contracts/fixtures (orchestrator)
	uv run python contracts/make_fixtures.py

schemas:          ## regenerează schemele JSON din contracts/ (orchestrator)
	uv run python -m cyberpunks.common.contracts export-schemas contracts

validate-fixtures:
	uv run cyberpunks validate contracts/fixtures/work_items_A.jsonl contracts/fixtures/work_items_B.jsonl contracts/fixtures/work_items_C.jsonl

# ---- A: contoare (firul Teo-A-contoare) ----
.PHONY: a-data a-train a-evaluate a-robustness a-select a-figures a-fusion a-report a-predict a-release a-test a-all
a-data:           ## A: descarcă SGCC și Low Carbon London (SHA-256), construiește features și eșantioanele
	uv run python -m cyberpunks.a_contoare.download
	uv run python -m cyberpunks.a_contoare.sgcc
	uv run python -m cyberpunks.a_contoare.lcl
a-train:          ## A: antrenează a-lgbm (Londra, probleme injectate) și a-lgbm-sgcc (SGCC, furt real)
	uv run python -m cyberpunks.a_contoare.train
a-evaluate:       ## A: evaluarea pe test separat -> reports/A/metrics.json, metrics_full.json, figuri
	uv run python -m cyberpunks.a_contoare.evaluate
a-robustness:     ## A: date lipsă 0-70% pe populația demo, SGCC pe timp -> reports/A/robustness.json
	uv run python -m cyberpunks.a_contoare.robustness
a-select:         ## A: alegerea features pe setul de calibrare -> reports/A/feature_selection.json
	uv run python -m cyberpunks.a_contoare.select_features
a-figures:        ## A: figurile pentru prezentare (reports/A/figures/headline_precision, ranking_at_k, false_alarms_...)
	uv run python -m cyberpunks.a_contoare.figures
a-fusion:         ## A: fuziunea cu bilanțul pe post, verificată pe testul A -> reports/A/fusion_check.json
	uv run python -m cyberpunks.a_contoare.fusion_check
a-report:         ## A: reports/A/error_analysis.md și model_card.md, generate din cifrele scripturilor
	uv run python -m cyberpunks.a_contoare.report
a-predict:        ## A: lucrările pentru demo-vara și maine (merge și fără a-data, din pachetul demo din git)
	uv run python -m cyberpunks.a_contoare.predict --scenario demo-vara
	uv run python -m cyberpunks.a_contoare.predict --scenario maine
a-release:        ## A: modelul și pachetul demo care intră în git (models/release/A, data/samples/A)
	uv run python -m cyberpunks.a_contoare.train --release
a-test:           ## A: testele firului A
	uv run pytest tests/a
a-all: a-data a-train a-evaluate a-robustness a-select a-predict a-figures a-fusion a-report  ## A: totul, de la zero (~9 minute)

# ---- B: furtună (firul Teo-B-furtuna) ----
.PHONY: b-data b-weather b-dataset b-repro b-evaluate b-predict b-reports b-test b-all

b-data:           ## B: descarcă EAGLE-I 2023-2025 (md5 verificat) și construiește tabelele pe ore
	uv run python -m cyberpunks.b_furtuna.download eaglei --years 2023-2025
	uv run python -m cyberpunks.b_furtuna.eaglei hourly --years 2023-2025

b-weather:        ## B (opțional, vremea e în git): reface vremea din Open-Meteo (~7.300 de apeluri, ~2 h)
	uv run python -m cyberpunks.b_furtuna.openmeteo us-history

b-dataset:        ## B (opțional, tabelul e în git): reface tabelul comitat × zi (cere make b-data)
	uv run python -m cyberpunks.b_furtuna.dataset

b-repro:          ## B, calea scurtă pentru juriu: reface metricile din tabelul din git, fără descărcări (~3 min)
	uv run python -m cyberpunks.b_furtuna.evaluate
	uv run cyberpunks validate reports/B/metrics.json

b-evaluate:       ## B: antrenare 2023-2024, test 2025 și state nevăzute -> reports/B/metrics.json
	uv run python -m cyberpunks.b_furtuna.evaluate

b-predict:        ## B: lucrările pentru demo-vara și maine
	uv run python -m cyberpunks.b_furtuna.predict --scenario demo-vara
	uv run python -m cyberpunks.b_furtuna.predict --scenario maine
	uv run cyberpunks validate outputs/work_items/demo-vara/B.jsonl outputs/work_items/maine/B.jsonl

b-reports:        ## B: toate rapoartele, din aceleași date (metrici, experimente, erori, backtest, model card)
	uv run python -m cyberpunks.b_furtuna.evaluate
	uv run python -m cyberpunks.b_furtuna.experiments
	uv run python -m cyberpunks.b_furtuna.error_analysis
	uv run python -m cyberpunks.b_furtuna.backtest
	uv run python -m cyberpunks.b_furtuna.model_card

b-test:           ## B: testele firului B (fără rețea)
	uv run pytest tests/b -q

b-all: b-data b-weather b-dataset b-reports b-predict

# ---- C: prosumatori (firul Teo-C-prosumatori) ----
.PHONY: c-weather c-bench c-sim c-population c-eval c-train c-predict c-figures c-test c-all
c-weather:        ## C: descarcă meteo Open-Meteo 2023-2026 (data/raw/C, sume de control în data/samples/C)
	uv run python -m cyberpunks.c_prosumatori.weather archive 2023-01-01 2026-11-06
c-bench:          ## C: calculul vectorizat față de pandapower, timpi (reports/C/powerflow_bench.json)
	uv run python -m cyberpunks.c_prosumatori.powerflow
c-sim:            ## C: simularea fizică a celor 480 de posturi de antrenare (data/processed/C/train), cel mult 4 procese
	uv run python -m cyberpunks.c_prosumatori.simulate pool train --n 80 --workers 4
c-population:     ## C: cele 300 de posturi demo pe hartă (OSM + sintetic) și simularea lor
	uv run python -m cyberpunks.c_prosumatori.population
c-eval:           ## C: evaluarea pe rețele nevăzute și luni nevăzute (reports/C/metrics.json), figurile
	uv run python -m cyberpunks.c_prosumatori.evaluate
	uv run python -m cyberpunks.c_prosumatori.figures
c-train:          ## C: modelele finale (models/C/bundle.joblib), fără ziua demo
	uv run python -m cyberpunks.c_prosumatori.train
c-predict:        ## C: lucrările pentru demo-vara și maine (C.jsonl, serii, scara de soluții), raportul ofertelor de baterii
	uv run python -m cyberpunks.c_prosumatori.predict --scenario demo-vara
	uv run python -m cyberpunks.c_prosumatori.predict --scenario maine
	uv run python -m cyberpunks.c_prosumatori.reports_c offers --scenario demo-vara
c-test:           ## C: testele firului C
	uv run pytest tests/c
c-all: c-weather c-sim c-population c-train c-predict c-eval  ## C: tot lanțul, de la date la lucrări (circa 15 minute)

# ---- Bilanț pe post (firul Teo-bilant) ----
.PHONY: bilant-data bilant-eval bilant-predict bilant-test
bilant-data:      ## Bilanț: lumea simulată, 600 de posturi cu probleme ascunse (data/processed/bilant), cel mult 4 procese
	uv run python -m cyberpunks.a_bilant.dataset --workers 4
bilant-eval:      ## Bilanț: modelele și metodele simple, reports/bilant/metrics.json, figurile, planul B, analiza erorilor
	uv run python -m cyberpunks.a_bilant.evaluate
	uv run python -m cyberpunks.a_bilant.planb
	uv run python -m cyberpunks.a_bilant.error_analysis
	uv run python -m cyberpunks.a_bilant.headline
bilant-predict:   ## Bilanț: lucrările A_bilant.jsonl, seriile și starea pentru fuziune, scenariul demo-vara
	uv run python -m cyberpunks.a_bilant.predict --scenario demo-vara
bilant-test:      ## Bilanț: testele firului
	uv run pytest tests/bilant

# ---- Planificator și API (firul Teo-planificator) ----
.PHONY: api api-dev run-demo test-planner agent-eval solver-bench demo-snapshot api-demo demo demo-offline

api:              ## API-ul agentului pe http://127.0.0.1:8710/api (documentație: /docs)
	uv run uvicorn cyberpunks.api.app:app --host 127.0.0.1 --port 8710

api-dev:          ## la fel, cu reîncărcare la fiecare schimbare de cod
	uv run uvicorn cyberpunks.api.app:app --host 127.0.0.1 --port 8710 --reload --reload-dir src

run-demo:         ## agentul cap-coadă pe scenariul demo-vara
	uv run cyberpunks run --scenario demo-vara

test-planner:     ## testele planificatorului și ale API-ului
	uv run pytest tests/planner

agent-eval:       ## evaluarea agentului față de strategii simple (reports/planner/agent_eval.json și .md)
	uv run python -m cyberpunks.planner.evaluate

solver-bench:     ## OR-Tools față de greedy pe 100-300 de lucrări (reports/planner/solver_benchmark.json)
	uv run python -m cyberpunks.planner.benchmark

demo-snapshot:    ## copiază planul demo-vara în outputs/demo/ (intră în git; interfața îl folosește ca rezervă)
	uv run python -m cyberpunks.planner.snapshot --scenario demo-vara

api-demo:         ## API-ul pe instantaneul din git (outputs/demo/), fără să ruleze modelele
	CYBERPUNKS_API_SOURCE=demo uv run uvicorn cyberpunks.api.app:app --host 127.0.0.1 --port 8710

demo:             ## DEMO: planul real pentru demo-vara, apoi API-ul (8710) și consola (3710), în paralel; Ctrl-C le oprește
	uv run cyberpunks run --scenario demo-vara
	$(MAKE) -j2 api web

demo-offline:     ## DEMO fără modele: API-ul pe instantaneul din git și consola, în paralel (fără Rulează și fără aprobări)
	$(MAKE) -j2 api-demo web

# ---- Interfață (firul Teo-ui) ----
.PHONY: web web-install web-build web-demo web-test web-smoke
web-install:      ## instalează dependențele consolei (bun; merge și npm install în web/)
	cd web && bun install
web: web-install  ## pornește consola dispecerului pe http://localhost:3710 (API-ul pe 8710 e opțional)
	cd web && bun run dev
web-demo: web-install  ## DEMO: consola în modul de producție pe http://localhost:3710 (build ~10 s, apoi pagini mai rapide, fără unelte de dezvoltare)
	cd web && bun run build && bun run start
web-build: web-install  ## build de producție al consolei
	cd web && bun run build
web-test:         ## testele consolei (stratul de date: API, instantaneu demo, fixture-uri)
	cd web && bun test
web-smoke:        ## încarcă toate ecranele pe consola pornită (make web) și cade la orice eroare
	cd web && bun run smoke

# ---- Prezentare (firul Teo-prezentare) ----
