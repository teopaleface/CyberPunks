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

# ---- B: furtună (firul Teo-B-furtuna) ----

# ---- C: prosumatori (firul Teo-C-prosumatori) ----
.PHONY: c-weather c-bench c-sim c-test
c-weather:        ## C: descarcă meteo Open-Meteo 2023-2026 (data/raw/C, sume de control în data/samples/C)
	uv run python -m cyberpunks.c_prosumatori.weather archive 2023-01-01 2026-11-06
c-bench:          ## C: calculul vectorizat față de pandapower, timpi (reports/C/powerflow_bench.json)
	uv run python -m cyberpunks.c_prosumatori.powerflow
c-sim:            ## C: simularea fizică a posturilor de antrenare (data/processed/C/train), cel mult 4 procese
	uv run python -m cyberpunks.c_prosumatori.simulate pool train --n 80 --workers 4
c-test:           ## C: testele firului C
	uv run pytest tests/c

# ---- Bilanț pe post (firul Teo-bilant) ----
.PHONY: bilant-data bilant-eval bilant-test
bilant-data:      ## Bilanț: lumea simulată, 600 de posturi cu probleme ascunse (data/processed/bilant), cel mult 4 procese
	uv run python -m cyberpunks.a_bilant.dataset --workers 4
bilant-eval:      ## Bilanț: modelele și metodele simple, reports/bilant/metrics.json și figurile
	uv run python -m cyberpunks.a_bilant.evaluate
bilant-test:      ## Bilanț: testele firului
	uv run pytest tests/bilant

# ---- Planificator și API (firul Teo-planificator) ----
.PHONY: api api-dev run-demo test-planner

api:              ## API-ul agentului pe http://127.0.0.1:8710/api (documentație: /docs)
	uv run uvicorn cyberpunks.api.app:app --host 127.0.0.1 --port 8710

api-dev:          ## la fel, cu reîncărcare la fiecare schimbare de cod
	uv run uvicorn cyberpunks.api.app:app --host 127.0.0.1 --port 8710 --reload --reload-dir src

run-demo:         ## agentul cap-coadă pe scenariul demo-vara
	uv run cyberpunks run --scenario demo-vara

test-planner:     ## testele planificatorului și ale API-ului
	uv run pytest tests/planner

# ---- Interfață (firul Teo-ui) ----

# ---- Prezentare (firul Teo-prezentare) ----
