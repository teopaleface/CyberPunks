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

# ---- Prezentare (firul Teo-prezentare) ----
.PHONY: presentation-assets music video-check video-preview video-preview-stop video-render
HF := npx -y hyperframes@0.9.19

presentation-assets:  ## harta de noapte NASA, granițele regiunilor, schița scenei cu agentul
	uv run python presentation/scripts/fetch_night_lights.py
	uv run --with shapely python presentation/scripts/build_map_overlay.py
	uv run --with shapely python presentation/scripts/build_s5_scene.py

music:                ## regenerează muzica originală a filmului (96 BPM, 30 s)
	uv run python presentation/music/compose.py

video-check:          ## verificările HyperFrames (lint, runtime, layout, contrast)
	cd presentation/video && $(HF) check

video-preview:        ## previzualizare pe portul 3720 (rămâne pornită în fundal)
	cd presentation/video && $(HF) preview --background --port 3720 --no-open

video-preview-stop:
	cd presentation/video && $(HF) preview --stop

video-render:         ## exportul final în presentation/exports/ (H.264, AAC 48 kHz, -16 LUFS)
	bash presentation/scripts/export_video.sh

