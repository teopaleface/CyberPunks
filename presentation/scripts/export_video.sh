#!/usr/bin/env bash
# Randează filmul cu HyperFrames și face exportul final:
# H.264 High, yuv420p, BT.709, AAC 48 kHz, loudnorm în două treceri la -16 LUFS / -1 dBTP, +faststart.
# Rulare din rădăcina repo-ului: bash presentation/scripts/export_video.sh [nume-ieșire]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VID="$ROOT/presentation/video"
OUT_DIR="$ROOT/presentation/exports"
NAME="${1:-tura-de-maine-30s}"
TMP="$VID/renders/tmp"
mkdir -p "$TMP" "$OUT_DIR"

cd "$VID"
npx -y hyperframes@0.9.19 render -o "$TMP/$NAME-raw.mp4" --quality delivery --workers 4

if ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$TMP/$NAME-raw.mp4" | grep -q audio; then
  # Trecerea 1: măsurăm loudness-ul.
  STATS=$(ffmpeg -hide_banner -nostats -i "$TMP/$NAME-raw.mp4" -vn \
    -af loudnorm=I=-16:TP=-1:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  MI=$(echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['input_i'])")
  MTP=$(echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['input_tp'])")
  MLRA=$(echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['input_lra'])")
  MTH=$(echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['input_thresh'])")
  OFF=$(echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['target_offset'])")
  # Trecerea 2: aplicăm corecția liniar, apoi AAC 48 kHz.
  ffmpeg -hide_banner -y -i "$TMP/$NAME-raw.mp4" -c:v copy \
    -af "loudnorm=I=-16:TP=-1:LRA=11:measured_I=$MI:measured_TP=$MTP:measured_LRA=$MLRA:measured_thresh=$MTH:offset=$OFF:linear=true,aresample=48000" \
    -c:a aac -b:a 256k -ar 48000 -movflags +faststart \
    -color_primaries bt709 -color_trc bt709 -colorspace bt709 "$OUT_DIR/$NAME.mp4"
else
  echo "Atenție: randarea nu are sunet; exportul rămâne fără sunet."
  ffmpeg -hide_banner -y -i "$TMP/$NAME-raw.mp4" -c:v copy -movflags +faststart "$OUT_DIR/$NAME.mp4"
fi

ffprobe -v error -show_entries stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,sample_rate,channels \
  -show_entries format=duration,size -of compact "$OUT_DIR/$NAME.mp4"
ffmpeg -hide_banner -nostats -i "$OUT_DIR/$NAME.mp4" -vn -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:" | tail -2 || true
