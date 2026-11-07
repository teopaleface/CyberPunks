#!/usr/bin/env bash
# Randează filmul cu HyperFrames și face exportul final, apoi îl verifică automat.
# Ținta: 1920x1080, 30 fps, H.264 High, yuv420p, BT.709, AAC 48 kHz stereo, -14 LUFS (proiector), vârf <= -1 dBTP,
# +faststart, sub 50 MB. Exportul se oprește cu eroare dacă lipsește sunetul sau dacă o verificare pică.
# Rulare din rădăcina repo-ului: bash presentation/scripts/export_video.sh [nume-ieșire] [director-ieșire]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VID="$ROOT/presentation/video"
NAME="${1:-tura-de-maine-30s}"
OUT_DIR="${2:-$ROOT/presentation/exports}"
TMP="$VID/renders/tmp"
TARGET_I=-14
TARGET_TP=-1
mkdir -p "$TMP" "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"  # cale absolută: mai jos lucrăm din directorul proiectului video
for tool in npx ffmpeg ffprobe python3 uv; do command -v "$tool" >/dev/null || { echo "Lipsește $tool din PATH." >&2; exit 1; }; done

# Cifrele din film se scriu din reports/ și outputs/demo/ (niciodată de mână).
(cd "$ROOT" && uv run python presentation/scripts/cifre_film.py)

cd "$VID"
npx -y hyperframes@0.9.19 render -o "$TMP/$NAME-raw.mp4" --quality delivery --workers 4

if ! ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$TMP/$NAME-raw.mp4" | grep -q audio; then
  echo "Randarea nu are sunet: exportul se oprește (verifică <audio id=\"music\"> din index.html)." >&2
  exit 1
fi

# Trecerea 1: măsurăm loudness-ul. Trecerea 2: corecția liniară, apoi AAC 48 kHz.
STATS=$(ffmpeg -hide_banner -nostats -i "$TMP/$NAME-raw.mp4" -vn \
  -af loudnorm=I=$TARGET_I:TP=$TARGET_TP:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
read -r MI MTP MLRA MTH OFF < <(echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['input_i'], d['input_tp'], d['input_lra'], d['input_thresh'], d['target_offset'])")
PASS2=$(ffmpeg -hide_banner -nostats -y -i "$TMP/$NAME-raw.mp4" -c:v copy \
  -af "loudnorm=I=$TARGET_I:TP=$TARGET_TP:LRA=11:measured_I=$MI:measured_TP=$MTP:measured_LRA=$MLRA:measured_thresh=$MTH:offset=$OFF:linear=true:print_format=json,aresample=48000" \
  -c:a aac -b:a 256k -ar 48000 -ac 2 -movflags +faststart \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 "$OUT_DIR/$NAME.mp4" 2>&1 | sed -n '/^{/,/^}/p')
NORM=$(echo "$PASS2" | python3 -c "import sys,json; print(json.load(sys.stdin)['normalization_type'])")
if [ "$NORM" != "linear" ]; then
  echo "Atenție: loudnorm a trecut în modul $NORM (nu liniar); verifică dinamica mixajului." >&2
fi

# Verificarea automată a fișierului final.
python3 - "$OUT_DIR/$NAME.mp4" "$TARGET_I" "$TARGET_TP" <<'PY'
import json, subprocess, sys, os, re
path, ti, ttp = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                                  capture_output=True, text=True, check=True).stdout)
v = next(s for s in probe["streams"] if s["codec_type"] == "video")
a = next(s for s in probe["streams"] if s["codec_type"] == "audio")
dur = float(probe["format"]["duration"]); size = int(probe["format"]["size"])
ebu = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
i_lufs = float(re.findall(r"I:\s+(-?\d+\.\d) LUFS", ebu)[-1]); tp = float(re.findall(r"Peak:\s+(-?\d+\.\d) dBFS", ebu)[-1])
with open(path, "rb") as f:
    head = f.read(4096)
faststart = head.find(b"moov") != -1 and (head.find(b"mdat") == -1 or head.find(b"moov") < head.find(b"mdat"))
checks = {
    "1920x1080": (v["width"], v["height"]) == (1920, 1080),
    "30 fps": v["r_frame_rate"] == "30/1",
    "H.264 High": v["codec_name"] == "h264" and v.get("profile") == "High",
    "yuv420p": v["pix_fmt"] == "yuv420p",
    "BT.709": v.get("color_primaries") == "bt709" and v.get("color_transfer") == "bt709" and v.get("color_space") == "bt709",
    "AAC 48 kHz stereo": a["codec_name"] == "aac" and a["sample_rate"] == "48000" and a["channels"] == 2,
    "durata 30,0 s": abs(dur - 30.0) < 0.05,
    "sub 50 MB": size < 50 * 1024 * 1024,
    "faststart": faststart,
    f"loudness {ti:+.0f} LUFS (+-1)": abs(i_lufs - ti) <= 1.0,
    f"vârf <= {ttp:.0f} dBTP": tp <= ttp + 0.05,
}
for k, ok in checks.items():
    print(("OK   " if ok else "PICĂ ") + k)
print(f"durata {dur:.3f} s, {size/1e6:.1f} MB, {i_lufs} LUFS, vârf {tp} dBTP")
sys.exit(0 if all(checks.values()) else 1)
PY
