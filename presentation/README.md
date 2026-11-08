# Prezentarea Daybreak: filmul, slideurile, scriptul demo-ului

| Ce | Unde |
|---|---|
| Filmul final, exportul versionat (52,9 s, 38,7 MB; vocea și efectele, fără muzică comercială) | `exports/daybreak-film.mp4`, făcut de `scripts/export_film_public.sh` |
| Filmul pentru sală (aceeași imagine, cu instrumentalul „POWER”) | `exports/local/daybreak-film-power.mp4`, doar local, nu e în git |
| Proiectul filmului (HyperFrames peste Three.js și Blender, vocea, efectele) | `frames-3d/` (`FILM_V3.md`, `threejs/film_v3/`, `audio/`) |
| Slideurile (16 pagini) | `exports/daybreak-slides.pdf`, făcute de `scripts/build_slides.py` din `reports/` |
| Scriptul demo-ului (5 min + 2 min întrebări, planul B) | `demo-script.md` |
| Înregistrarea de rezervă a consolei | `exports/local/daybreak-demo-rezerva.mp4`, doar local |
| Creditele și sursele | `CREDITS.md` |
| Variantele vechi ale filmului (istoric) | `video/`, `music/`, `brand-lab/`, `frames-codex/` |

## Cerințe

- macOS sau Linux, `bash`, `python3`, `uv` (Python 3.12 din `.python-version`), Node.js 20+ cu `npx` (folosit: v26.8.1), `ffmpeg` și `ffprobe` (folosit: 8.x).
- HyperFrames e fixat la 0.9.19 și se rulează cu `npx -y hyperframes@0.9.19`; își descarcă singur Chrome-ul de randare la prima rulare (`npx -y hyperframes@0.9.19 browser ensure`).
- Pentru captura consolei: interfața (`make web`, portul 3710), API-ul (`make api`, portul 8710) și `agent-browser`.
- Pentru activele variantei 1 (opțional): `shapely`, adus temporar cu `uv run --with shapely`.

## Comenzi (din rădăcina repo-ului)

```bash
uv run python presentation/scripts/build_slides.py   # slideurile: cifrele din reports/, PDF-ul în presentation/exports/
bash presentation/scripts/export_film_public.sh       # filmul versionat (fără „POWER”) și copia locală pentru sală
make presentation-assets   # cifrele din film, citite din reports/ și outputs/demo/
make video-check           # verificările HyperFrames
make video-preview         # previzualizare pe portul 3720 (oprire: make video-preview-stop)
make video-render          # exportul final în presentation/exports/, verificat automat (format, -14 LUFS, faststart)
make music                 # refacerea muzicii (identică bit cu bit)
bash presentation/scripts/capture_consola.sh   # captura consolei reale la rezoluție dublă
```
