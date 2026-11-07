#!/usr/bin/env bash
# Capturează consola reală la rezoluție dublă (3840x2160), pentru film și slideuri.
# Cere interfața pornită (make web, portul 3710) și API-ul (make api, portul 8710), scenariul demo-vara.
# Rulare din rădăcina repo-ului: bash presentation/scripts/capture_consola.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/presentation/video/assets/ui"
mkdir -p "$OUT"
export AGENT_BROWSER_SESSION=prez-real
agent-browser set viewport 1920 1080 2
shot() { agent-browser open "http://localhost:3710$1" >/dev/null; sleep 7; agent-browser screenshot "$OUT/$2" >/dev/null; echo "$2 <- $1"; }
shot / consola_reala@2x.png
agent-browser close >/dev/null || true
