# Status: Teo-prezentare
Actualizat: 2026-11-07 13:35
Milestone curent: M0 gata; urmează v0 animat cu muzică (19:00)
Gata de merge: nu (doar `presentation/`, Makefile și status; nu atinge codul comun)

## Făcut
- 12:50 Citite instrucțiunile, memoria, planul și contractele. `uv sync` și `make check` trec.
- 12:58 HyperFrames 0.9.19 instalat local (`presentation/video/`). Testul de 2 secunde randat: H.264 High, 1920×1080, 30 fps, yuv420p, 60 de cadre, diacriticele ș ț corecte (randat în 3,4 s).
- 13:00 Articolul lui leo citit integral; regulile și aplicarea lor în `presentation/STYLE.md` (3 culori: noapte #07090D, hârtie #F2EFE8, chihlimbar #FFA53D; font Hanken Grotesk, OFL).
- 13:00 Codex (image 2.6) a generat 5 imagini (contor, stâlp cu transformator, panouri solare, furtună, zori), prompturile în `presentation/assets/gen/PROMPTS.md`.
- 13:05 Harta reală a României noaptea (NASA Black Marble 2016, GIBS) cu cele 3 regiuni Rețele Electrice conturate (geoBoundaries, CC BY 4.0).
- 13:15 Cele 8 scene ale filmului scrise și animate (schiță), `hyperframes check` trece cu 0 erori. Storyboard-ul (11 cadre statice) în `presentation/video/STORYBOARD.md` și `presentation/video/boards/storyboard.html`.
- 13:20 Storyboard-ul arătat lui Teo (11 cadre) și prima variantă animată, fără muzică.
- 13:35 Filmul trece pe sistemul produsului, după răspunsul orchestratorului: font Archivo (ca în consolă), fundal cerneala logoului #0B1622, text hârtie #F5F4F0, logoul "răsărit pe traseu" animat la nume și la final, markerii surselor A/B/C în culorile consolei. Chihlimbarul rămâne doar pentru soarele din logo, zori și sursa C; traseele și opririle agentului sunt în hârtie. Ziua reală 8 iulie 2025 apare în scena semnalelor (vijelie în Banat, tensiune la prânz în București). `hyperframes check` trece.
- Muzica originală (96 BPM, 12 măsuri = 30 s) e aproape gata la un subagent.

## Urmează
- Arăt storyboard-ul lui Teo (gata înainte de 15:00).
- Muzica intră în film; v0 animat complet și randat până la 19:00.
- Scriptul demo-ului (5 min) și scheletul slideurilor.
- După 01:00: capturi reale din consolă (cadrele 5 și 6); după 21:30: cifra față de baseline din `reports/` (cadrul 7).

## Blocaje
- Niciunul.

## Cereri către orchestrator
- (rezolvat 13:20) Harta întunecată și cardul "Nu sunt sigur" în `/demo`: cerute interfeței de orchestrator. Mulțumesc.
- (rezolvat 13:20) Cifra principală: valoarea capturată din `reports/planner/agent_eval.json` față de cea mai bună strategie simplă; în slideuri și metrica principală a fiecărui model din `reports/<X>/metrics.json`.
- Nou: când există `reports/planner/agent_eval.json` și `reports/<A|B|C>/metrics.json` în `Teo`, vă rog spuneți-mi (sau le iau eu la verificarea de la 21:30).

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
- 13:12 Chihlimbarul e rezervat acțiunilor agentului (punctul, traseele, "Act", cifra noastră). ÎNLOCUITĂ la 13:35.
- 13:35 Produsul are prioritate: filmul preia fontul (Archivo), cerneala, hârtia și logoul interfeței. Acțiunile agentului sunt în hârtie (alb), ca traseele în cerneală din consolă; chihlimbarul doar pentru soare, zori și sursa C. Filmul rămâne pe fundal închis (noaptea → zorii), iar capturile deschise din consolă vor intra ca "ecranul dispecerului".
- 13:35 Scena semnalelor are 3,75 s (1,25 s pe semnal, ca textele să se poată citi), scena agentului 6,25 s; pașii Perceive, Estimate, Decide, Act cad la 16,25 / 17,5 / 18,75 / 20,0 s.
