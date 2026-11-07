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
.PHONY: presentation-assets music video-check video-preview video-preview-stop video-render
HF := npx -y hyperframes@0.9.19

presentation-assets:  ## harta de noapte NASA, granițele regiunilor, schița scenei cu agentul
	uv run python presentation/scripts/fetch_night_lights.py
	uv run --with shapely python presentation/scripts/build_map_overlay.py
	uv run --with shapely python presentation/scripts/build_s5_scene.py

music:                ## regenerează muzica originală a filmului (96 BPM, 30 s) și o pune în proiectul video
	uv run python presentation/music/compose.py
	ffmpeg -v error -y -i presentation/music/out/tura_96bpm_30s.wav -c:a flac -sample_fmt s16 presentation/video/assets/audio/tura_96bpm_30s.flac

video-check:          ## verificările HyperFrames (lint, runtime, layout, contrast)
	cd presentation/video && $(HF) check

video-preview:        ## previzualizare pe portul 3720 (rămâne pornită în fundal)
	cd presentation/video && $(HF) preview --background --port 3720 --no-open

video-preview-stop:
	cd presentation/video && $(HF) preview --stop

video-render:         ## exportul final în presentation/exports/ (H.264, AAC 48 kHz, -16 LUFS)
	bash presentation/scripts/export_video.sh

