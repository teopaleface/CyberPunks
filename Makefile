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
.PHONY: b-data b-weather b-dataset b-evaluate b-predict b-test b-all

b-data:           ## B: descarcă EAGLE-I 2023-2025 (md5 verificat) și construiește tabelele pe ore
	uv run python -m cyberpunks.b_furtuna.download eaglei --years 2023-2025
	uv run python -m cyberpunks.b_furtuna.eaglei hourly --years 2023-2025

b-weather:        ## B: vremea istorică Open-Meteo pentru cele 80 de comitate (~6.300 de apeluri, în ritm lent)
	uv run python -m cyberpunks.b_furtuna.openmeteo us-history

b-dataset:        ## B: tabelul comitat × zi
	uv run python -m cyberpunks.b_furtuna.dataset

b-evaluate:       ## B: antrenare 2023-2024, test 2025 și state nevăzute -> reports/B/metrics.json
	uv run python -m cyberpunks.b_furtuna.evaluate

b-predict:        ## B: lucrările pentru demo-vara și maine
	uv run python -m cyberpunks.b_furtuna.predict --scenario demo-vara
	uv run python -m cyberpunks.b_furtuna.predict --scenario maine
	uv run cyberpunks validate outputs/work_items/demo-vara/B.jsonl outputs/work_items/maine/B.jsonl

b-test:           ## B: testele firului B (fără rețea)
	uv run pytest tests/b -q

b-all: b-data b-weather b-dataset b-evaluate b-predict

# ---- C: prosumatori (firul Teo-C-prosumatori) ----

# ---- Planificator și API (firul Teo-planificator) ----

# ---- Interfață (firul Teo-ui) ----

# ---- Prezentare (firul Teo-prezentare) ----
