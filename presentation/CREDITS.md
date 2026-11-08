# Credite și surse: video, slideuri, demo

Tot ce apare în materialele de prezentare, cu sursa și licența. Ce e generat cu AI e marcat ca atare și pe ecran ("Imagini generate cu AI"); ce e sintetic e marcat "date sintetice".

## Filmul final: Daybreak (8 nov. 2026)

| Ce | Sursa și licența |
|---|---|
| Imaginea: cele 10 planșe „lume în miniatură” (același sat) | Generate cu AI (Codex, unealta de imagine; modelul nu e raportat de unealtă), mărite cu Real-ESRGAN (licențele în `frames-3d/plates_v3/`). Prompturile: `frames-3d/plates_v3/PROMPTS.md` și `prompts.json` |
| Obiectele 3D (camionul, contorul cu magnet, stâlpul rupt, panoul solar, casca, acele, norul) | Modelate de agenți AI în Blender, procedural (`frames-3d/objects/`) |
| Planeta și drumul camerei | Three.js (MIT) și Blender (`frames-3d/threejs/`) |
| Vocea (engleză) | Kokoro-82M v1.0 (Apache-2.0), prin kokoro-onnx 0.6.1, rulat local; vocea `af_heart`. Detalii: `frames-3d/audio/README.md` |
| Efectele sonore | Procedurale, generate în cod (`frames-3d/audio/tools/build.py`) |
| Muzica | Exportul versionat (`exports/daybreak-film.mp4`) nu are muzică. Doar copia pentru sală, care rămâne locală și nu e distribuită, folosește instrumentalul „POWER” (Kanye West); piesa nu e în git |
| Interfața din film | Ilustrativă, în stilul consolei Daybreak; consola reală se arată live la demo |
| Cifrele din film | „30% less driving” (10.515 față de 15.439 km, -31,9%) și „fewer wasted trips” (37% față de 63%): `reports/planner/agent_eval.json`, simulare de 30 de zile, față de „primul venit, primul servit”. „Eleven crews”: `config/crews.yaml`. „556 problems”: consola, scenariul sintetic `demo-vara`, 7 nov. |
| Slideurile | Imaginile de pe slideurile 1 și 16 sunt planșe generate cu AI (etichetat pe slide); cifrele vin din `reports/` prin `scripts/build_slides.py` |

## Unelte

- HyperFrames 0.9.19 (HeyGen, open source): HTML randat în MP4. Proiectul e în `video/`.
- GSAP 3.15.0 (GreenSock), licența standard fără cost (https://gsap.com/standard-license), inclus local în `video/assets/vendor/gsap-3.15.0.min.js` (SHA-256 `92bb9a96476f983d212a2bc4f54c889039c1696dd4461d40a736860938570fbb`).
- Codex (OpenAI), unealta de imagine (modelul pe care echipa îl numește "image 2.6"; metadatele imaginilor spun "gpt-image"), modelele GPT-6.1 Sol și GPT-6 Astra.
- Blender 5.2.1 (pentru obiectele 3D modelate de agenți, în lucru).
- ffmpeg: exportul final (loudnorm, AAC, faststart).

## Filmul, varianta 2 (istoric, nu mai e în export)

| Fișier | Ce e | Sursa și licența |
|---|---|---|
| `video/assets/ui/consola_reala@2x.png` | Consola dispecerului "Tura de mâine", planul agentului pentru 8 iulie 2025 | Captură din aplicația echipei (http://localhost:3710/), date sintetice pe hartă reală. Harta: OpenFreeMap, © OpenMapTiles, date © contribuitorii OpenStreetMap (ODbL); atribuirea apare în colțul hărții din consolă. Script: `scripts/capture_consola.sh` |
| `video/assets/3d/obj_*.png` | Contor, nor de furtună, panou solar, transformator, cască | Generate cu AI (Codex, GPT-6.1 Sol, 7 nov. 2026), fundal transparent. Prompturile exacte: `assets/gen3d/PROMPTS.md` |
| `video/assets/brand/logo-a*.svg` | Logoul "Tura de mâine" ("răsărit pe traseu") | Firul UI al echipei: concept generat cu Codex, SVG desenat de mână. Proveniența și prompturile: `web/public/brand/README.md` |
| `video/compositions/k6-lucrare.html`, `k7-tensiune.html` | Curbele bilanțului și ale tensiunii | Ilustrative, date sintetice (etichetat pe ecran); seria de tensiune vine din fixture-ul sintetic `contracts/fixtures/series_C-20261109-PT-1432.json` |

Cifrele din film nu se scriu de mână: `scripts/cifre_film.py` le citește din `reports/planner/agent_eval.json` (cifra față de cea mai bună strategie simplă) și din `outputs/demo/plans/demo-vara/plan.json` (numărul de echipe) și le scrie în scene, la fiecare export.

## Varianta 1 a filmului (păstrată în istoric, nu mai e în export)

| Fișier | Ce e | Sursa și licența |
|---|---|---|
| `video/assets/img/romania_night_z8.jpg` | România noaptea, din satelit | NASA Earth Observatory, VIIRS Black Marble 2016, prin NASA GIBS (date publice NASA). Script: `scripts/fetch_night_lights.py` |
| `video/assets/geo/*.svg`, `regions.json` | Granițele României și ale celor trei regiuni Rețele Electrice | geoBoundaries ROU ADM1, sursa Banca Mondială (https://www.geoboundaries.org/), licență CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Modificări: limitele județelor au fost reunite pe regiuni, simplificate și reproiectate în pixelii imaginii NASA. Script: `scripts/build_map_overlay.py` |
| `video/assets/img/gen-*.jpg` | Contor, stâlp cu transformator, panouri solare, front de furtună, câmpie în zori | Generate cu AI (Codex, 7 nov. 2026). Prompturile exacte: `assets/gen/PROMPTS.md` |

## Font

- Archivo (The Archivo Project Authors, Omnibus-Type), SIL Open Font License 1.1, același font ca în consola dispecerului. Fișierele și licența: `video/assets/fonts/`.

## Muzica variantelor vechi (istoric)

- Originală, compusă în cod de echipă pentru acest proiect, fără sample-uri: `music/compose.py` (varianta 1, 96 BPM) și `music/compose_kinetic.py` (varianta 2, 120 BPM, în lucru). Licență CC0.

## Texte și cifre

- "Un scor de 0,87 ... nu e un plan": pornește de la documentul oficial al temei PPC, "Un scor de anomalie de 0,87 nu îi spune unui tehnician unde să meargă mâine dimineață" (`memory/07-tema-ppc.md`).
- Ziua demo-ului, marți, 8 iulie 2025 (cod roșu ANM de vijelii în Banat, caniculă în București): sursele de presă și vremea verificată sunt în `docs/research/B.md`. Problemele A și C din acea zi sunt scenarii sintetice, nu observații reale.
- Cifrele modelelor și ale agentului: doar din `reports/`, cu comanda care le refăce (vezi `README.md` din rădăcină).

## Stil

- Regulile din articolul lui leo (@leomeethewoo), "Make your product videos look expensive (Apple Framework)", 25 sep. 2026. Rezumatul și aplicarea lor: `STYLE.md`.
- Gramatica filmului de referință dat de Teo (un film Trust Wallet): `research/REFERINTA-trust.md`. Fișierul de referință nu intră în git.
