# Status: Teo-prezentare
Actualizat: 2026-11-07 13:20
Milestone curent: M0 gata; urmează v0 animat cu muzică (19:00)
Gata de merge: nu (doar `presentation/`, Makefile și status; nu atinge codul comun)

## Făcut
- 12:50 Citite instrucțiunile, memoria, planul și contractele. `uv sync` și `make check` trec.
- 12:58 HyperFrames 0.9.19 instalat local (`presentation/video/`). Testul de 2 secunde randat: H.264 High, 1920×1080, 30 fps, yuv420p, 60 de cadre, diacriticele ș ț corecte (randat în 3,4 s).
- 13:00 Articolul lui leo citit integral; regulile și aplicarea lor în `presentation/STYLE.md` (3 culori: noapte #07090D, hârtie #F2EFE8, chihlimbar #FFA53D; font Hanken Grotesk, OFL).
- 13:00 Codex (image 2.6) a generat 5 imagini (contor, stâlp cu transformator, panouri solare, furtună, zori), prompturile în `presentation/assets/gen/PROMPTS.md`.
- 13:05 Harta reală a României noaptea (NASA Black Marble 2016, GIBS) cu cele 3 regiuni Rețele Electrice conturate (geoBoundaries, CC BY 4.0).
- 13:15 Cele 8 scene ale filmului scrise și animate (schiță), `hyperframes check` trece cu 0 erori. Storyboard-ul (11 cadre statice) în `presentation/video/STORYBOARD.md` și `presentation/video/boards/storyboard.html`.
- Muzica originală (96 BPM, 12 măsuri = 30 s) e în lucru la un subagent.

## Urmează
- Arăt storyboard-ul lui Teo (gata înainte de 15:00).
- Muzica intră în film; v0 animat complet și randat până la 19:00.
- Scriptul demo-ului (5 min) și scheletul slideurilor.
- După 01:00: capturi reale din consolă (cadrele 5 și 6); după 21:30: cifra față de baseline din `reports/` (cadrul 7).

## Blocaje
- Niciunul.

## Cereri către orchestrator
- Pentru firul UI (până la modul `/demo` de la 01:00): o hartă întunecată în modul de prezentare, ca filmul să treacă lin din imaginea de noapte în consolă; un card "Nu sunt sigur" vizibil pentru captură. Dacă interfața alege alt font sau alt accent, spuneți-mi: filmul și slideurile le preiau (culorile sunt variabile în `presentation/video/index.html`).
- Ce cifră e "cifra principală față de baseline" pentru film și slideuri? Propunerea mea: din evaluarea agentului (`reports/planner/agent_eval.json`, valoarea capturată față de cea mai bună strategie simplă) sau PR-AUC-ul modelului A față de baseline (`reports/A/metrics.json`). Aștept să apară în `reports/`.

## Cum se rulează (comenzile exacte)
- `make presentation-assets` (harta NASA, granițele, schița scenei 5)
- `make video-check` (verificările HyperFrames)
- `make video-preview` (previzualizare pe portul 3720), `make video-preview-stop`
- `make video-render` (exportul final în `presentation/exports/`)
- `make music` (după ce intră `presentation/music/compose.py`)

## Cifre (doar din scripturi, cu comanda)
- În film apar doar cifrele PPC (2 milioane de contoare, 192 de milioane de citiri pe zi, scorul 0,87 din tema PPC). Cadrul 7 așteaptă cifra din `reports/`.

## Decizii (cu ora)
- 12:50 Video fără voce, doar text pe ecran și muzică originală.
- 12:58 Font Hanken Grotesk (OFL), ales dintre 6 fonturi testate în randare pentru ș/ț corecte și aspect apropiat de stilul Apple.
- 13:05 Deschiderea pe imaginea reală NASA a României noaptea, nu pe un fundal negru gol: e locul real al celor 2 milioane de contoare.
- 13:10 Cele 4 pași Perceive, Estimate, Decide, Act se văd pe hartă, în scena agentului, nu într-un cadru separat: o idee pe cadru, iar harta arată chiar pașii.
- 13:10 CARTO nu mai dă hărți fără cheie; scena 5 e o schiță vectorială cu date sintetice, etichetată, până la captura din consolă.
- 13:12 Chihlimbarul e rezervat acțiunilor agentului (punctul, traseele, "Act", cifra noastră).
