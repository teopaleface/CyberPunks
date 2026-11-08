#!/usr/bin/env bash
# Exportul VERSIONAT al filmului Daybreak (cel care intră în git și la predare): imaginea filmului v3, cu sunetul
# FĂRĂ piesa comercială „POWER”: vocea (Kokoro, af_heart) + efectele, la -14 LUFS, vârf <= -1 dBTP.
# Varianta cu „POWER”, pentru sală, rămâne locală: presentation/exports/local/daybreak-film-power.mp4.
# Rulare din rădăcina repo-ului: bash presentation/scripts/export_film_public.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
P="$ROOT/presentation"
DRAFT="$P/frames-3d/threejs/film_v3/renders/local/daybreak_v3_draft.mp4"   # randarea filmului v3 (imaginea)
VO="$P/frames-3d/audio/vo/vo_af_heart.wav"                                 # vocea, în timpul filmului
SFX="$P/frames-3d/audio/sfx_stem.wav"                                      # efectele, în timpul filmului
OUT="$P/exports/daybreak-film.mp4"
LOCAL="$P/exports/local/daybreak-film-power.mp4"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
for f in "$DRAFT" "$VO" "$SFX"; do [ -f "$f" ] || { echo "Lipsește $f" >&2; exit 1; }; done
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$DRAFT")

# 1) Mixajul fără muzică: vocea + efectele, adunate la nivelurile lor din mixajul filmului, întinse pe durata imaginii.
ffmpeg -hide_banner -loglevel error -y -i "$VO" -i "$SFX" \
  -filter_complex "[0:a][1:a]amix=inputs=2:normalize=0:duration=longest,apad=whole_dur=$DUR,atrim=0:$DUR[a]" \
  -map "[a]" -c:a pcm_s24le "$TMP/mix.wav"

# 2) Loudness: trecerea 1 măsoară, trecerea 2 corectează liniar (-14 LUFS, vârf -1 dBTP), apoi AAC 48 kHz.
STATS=$(ffmpeg -hide_banner -nostats -i "$TMP/mix.wav" -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
read -r MI MTP MLRA MTH OFF < <(echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['input_i'], d['input_tp'], d['input_lra'], d['input_thresh'], d['target_offset'])")
ffmpeg -hide_banner -loglevel error -y -i "$DRAFT" -i "$TMP/mix.wav" -map 0:v:0 -map 1:a:0 -c:v copy \
  -af "loudnorm=I=-14:TP=-1:LRA=11:measured_I=$MI:measured_TP=$MTP:measured_LRA=$MLRA:measured_thresh=$MTH:offset=$OFF:linear=true,aresample=48000" \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart -t "$DUR" "$OUT"

# 3) Copia pentru sală, cu „POWER” (doar locală, ignorată de git): același fișier, cu moov la început.
mkdir -p "$(dirname "$LOCAL")"
ffmpeg -hide_banner -loglevel error -y -i "$DRAFT" -c copy -movflags +faststart "$LOCAL"

# 4) Verificarea automată.
python3 - "$OUT" "$DUR" <<'PY'
import json, re, subprocess, sys
path, want = sys.argv[1], float(sys.argv[2])
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path], capture_output=True, text=True, check=True).stdout)
v = next(s for s in pr["streams"] if s["codec_type"] == "video"); a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
dur, size = float(pr["format"]["duration"]), int(pr["format"]["size"])
ebu = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
i_lufs = float(re.findall(r"I:\s+(-?\d+\.\d) LUFS", ebu)[-1]); tp = float(re.findall(r"Peak:\s+(-?\d+\.\d) dBFS", ebu)[-1])
head = open(path, "rb").read(65536)
checks = {
    "1920x1080, 30 fps": (v["width"], v["height"], v["r_frame_rate"]) == (1920, 1080, "30/1"),
    "H.264, yuv420p, BT.709": v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p" and v.get("color_primaries") == "bt709",
    "AAC 48 kHz stereo": a["codec_name"] == "aac" and a["sample_rate"] == "48000" and a["channels"] == 2,
    f"durata {want:.1f} s": abs(dur - want) < 0.1,
    "sub 50 MB": size < 50 * 1024 * 1024,
    "-14 LUFS (+-1)": abs(i_lufs + 14) <= 1.0,
    "vârf <= -1 dBTP": tp <= -0.95,
    "faststart": head.find(b"moov") != -1 and (head.find(b"mdat") == -1 or head.find(b"moov") < head.find(b"mdat")),
}
for k, ok in checks.items():
    print(("OK   " if ok else "PICĂ ") + k)
print(f"{path}: {dur:.2f} s, {size/1e6:.1f} MB ({size/1048576:.1f} MiB), {i_lufs} LUFS, vârf {tp} dBTP")
sys.exit(0 if all(checks.values()) else 1)
PY
ls -la "$LOCAL" | awk '{printf "Copia pentru sală (cu POWER, locală): %s, %.1f MB\n", $9, $5/1e6}'
