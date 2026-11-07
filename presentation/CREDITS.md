# Credite și surse: video, slideuri, demo

Tot ce apare în materialele de prezentare, cu sursa și licența. Ce e generat cu AI e marcat ca atare și pe ecran ("Imagine generată cu AI").

## Unelte

- HyperFrames 0.9.19 (HeyGen, open source): HTML randat în MP4. Proiectul e în `video/`.
- Codex (OpenAI), unealta de imagine (modelul pe care echipa îl numește "image 2.6"; metadatele imaginilor spun "gpt-image"): cele 5 imagini de produs și fundaluri.
- ffmpeg: exportul final (loudnorm, AAC, faststart).

## Imagini

| Fișier | Ce e | Sursa și licența |
|---|---|---|
| `video/assets/img/romania_night_z8.jpg` | România noaptea, din satelit | NASA Earth Observatory, VIIRS Black Marble 2016, prin NASA GIBS (date publice NASA). Script: `scripts/fetch_night_lights.py` |
| `video/assets/geo/*.svg`, `regions.json` | Granițele României și ale celor trei regiuni Rețele Electrice | geoBoundaries ROU ADM1 (Banca Mondială), CC BY 4.0. Script: `scripts/build_map_overlay.py` |
| `video/assets/img/gen-*.jpg` | Contor, stâlp cu transformator, panouri solare, front de furtună, câmpie în zori | Generate cu AI (Codex, 7 nov. 2026). Prompturile exacte: `assets/gen/PROMPTS.md` |
| `video/compositions/s5-agent.html` | Harta București-Ilfov cu lucrări și trasee | Schiță cu date SINTETICE, generată de `scripts/build_s5_scene.py`; se înlocuiește cu captura reală din consola dispecerului |

## Font

- Hanken Grotesk (The Hanken Grotesk Project Authors), SIL Open Font License 1.1. Fișierele și licența: `video/assets/fonts/`.

## Muzică

- Originală, compusă în cod de echipă pentru acest proiect, fără sample-uri: `music/compose.py`. Licență CC0.

## Texte și cifre

- "2 milioane de contoare inteligente", "192 de milioane de citiri pe zi": prezentarea PPC de la SmartHack XI 2026 (`memory/08-ppc-workshop-ai.md`).
- "Un scor de anomalie de 0,87 nu îi spune unui tehnician unde să meargă mâine dimineață": documentul oficial al temei PPC (`memory/07-tema-ppc.md`).
- Cifrele modelelor și ale agentului: doar din `reports/`, cu comanda care le refăce (vezi `README.md` din rădăcină).

## Stil

- Regulile din articolul lui leo (@leomeethewoo), "Make your product videos look expensive (Apple Framework)", 25 sep. 2026. Rezumatul și aplicarea lor: `STYLE.md`.
