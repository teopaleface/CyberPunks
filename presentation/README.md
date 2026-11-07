# Prezentarea: filmul de 30 de secunde, slideurile, scriptul demo-ului

| Ce | Unde |
|---|---|
| Filmul (HyperFrames) | `video/` (rădăcina `index.html`, scenele `compositions/k1-k9`, planul `video/STORYBOARD.md`) |
| Stilul și regulile | `STYLE.md`, studiul referinței `research/REFERINTA-trust.md` |
| Muzica (compusă în cod, CC0) | `music/` |
| Slideurile | `slides/` (planul în `slides/OUTLINE.md`) |
| Scriptul demo-ului | `demo-script.md` |
| Creditele și sursele | `CREDITS.md` |
| Exporturile finale (MP4, PDF) | `exports/` |

## Cerințe

- macOS sau Linux, `bash`, `python3`, `uv` (Python 3.12 din `.python-version`), Node.js 20+ cu `npx` (folosit: v26.8.1), `ffmpeg` și `ffprobe` (folosit: 8.x).
- HyperFrames e fixat la 0.9.19 și se rulează cu `npx -y hyperframes@0.9.19`; își descarcă singur Chrome-ul de randare la prima rulare (`npx -y hyperframes@0.9.19 browser ensure`).
- Pentru captura consolei: interfața (`make web`, portul 3710), API-ul (`make api`, portul 8710) și `agent-browser`.
- Pentru activele variantei 1 (opțional): `shapely`, adus temporar cu `uv run --with shapely`.

## Comenzi (din rădăcina repo-ului)

```bash
make presentation-assets   # cifrele din film, citite din reports/ și outputs/demo/
make video-check           # verificările HyperFrames
make video-preview         # previzualizare pe portul 3720 (oprire: make video-preview-stop)
make video-render          # exportul final în presentation/exports/, verificat automat (format, -14 LUFS, faststart)
make music                 # refacerea muzicii (identică bit cu bit)
bash presentation/scripts/capture_consola.sh   # captura consolei reale la rezoluție dublă
```
