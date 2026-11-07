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

# ---- Planificator și API (firul Teo-planificator) ----

# ---- Interfață (firul Teo-ui) ----

# ---- Prezentare (firul Teo-prezentare) ----
