#!/bin/sh
# Daybreak v3: rebuild everything from the latest feeds and render a draft.
#   sh render/v3_refresh.sh            (from presentation/frames-3d/threejs)
# 1 plates (plates_v3/ or placeholders) 2 timing (audio/timing.json or estimate)
# 3 lint 4 seam gate 5 render (draft, with the mix when present) 6 one-frame-per-scene strip
set -e
cd "$(dirname "$0")/.."
python3 render/sync_objects.py >/dev/null
cp -R film/assets/objects/. film_v3/assets/objects/
python3 render/v3_plates.py
if [ -f ../audio/local/daybreak_mix.m4a ]; then cp ../audio/local/daybreak_mix.m4a film_v3/assets/audio/local/; fi
node render/v3_build.mjs
cd film_v3
npx hyperframes lint
node ../render/seam-gate-synced.mjs verify --ledger ledger.json --project . | grep -E "■|FAIL|WARN|SEAM GATE"
OUT=renders/local/daybreak_v3_draft.mp4
npx hyperframes render --quality draft -o "$OUT" | tail -3
ffprobe -v error -show_entries format=duration -show_entries stream=codec_name,width,height -of compact "$OUT"
node ../render/v3_strip.mjs "$OUT"
