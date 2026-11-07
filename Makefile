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

# ---- Planificator și API (firul Teo-planificator) ----

# ---- Interfață (firul Teo-ui) ----
.PHONY: web web-install web-build web-test
web-install:      ## instalează dependențele consolei (bun; merge și npm install în web/)
	cd web && bun install
web: web-install  ## pornește consola dispecerului pe http://localhost:3710 (API-ul pe 8710 e opțional)
	cd web && bun run dev
web-build: web-install  ## build de producție al consolei
	cd web && bun run build
web-test:         ## testele consolei (stratul de date: API, instantaneu demo, fixture-uri)
	cd web && bun test

# ---- Prezentare (firul Teo-prezentare) ----
