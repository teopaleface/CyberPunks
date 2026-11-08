# Firul Prezentare: video de 30 de secunde (HyperFrames), slideuri, scriptul demo-ului

Branch: `Teo-prezentare`. Status: `status/Teo-prezentare.md`.

## Ce deții

`presentation/` (tot), secțiunea Prezentare din `Makefile`, `status/Teo-prezentare.md`.

## Video de 30 de secunde, în stil "Apple"

- Unealta: HyperFrames (pachetul npm `hyperframes`, ultima versiune 0.9.19: HTML → MP4, făcut pentru agenți; Teo l-a mai folosit, are cache în `~/.hyperframes`). Citește documentația și registrul de blocuri și componente. Lecții din wiki-ul lui Teo (`~/Documents/LLM-Wiki/wiki/vendors/higgsfield.md`): video-urile nu se pun într-un wrapper cu `data-start`, iar `data-media-start` stă pe grila de cadre; fontul Didot nu are ș și ț (Bodoni 72, Baskerville, Georgia și Avenir Next le au). Previzualizare pe portul 3720.
- Stilul: articolul "Make your product videos look expensive (Apple Framework)" scris de leo (@leomeethewoo, 25 sep. 2026, circa 2 milioane de vizualizări, https://x.com/leomeethewoo/status/2103529310208606701). Regulile lui:
  - intenție în orice alegere: font, fundal, muzică, culori; nimic întâmplător;
  - 3 culori pentru tot video-ul; fără efecte și sunete inutile;
  - întâi designul: storyboard cadru cu cadru, înainte de animație;
  - un cadru = o idee; fiecare scenă are spațiu să respire; obiectul principal în centru; fundalul nu concurează cu el;
  - mișcare cu easing (nimic liniar), mișcări suprapuse; tranziții fluide între scene, nu tăieturi directe;
  - ritm adaptat: accelerează, încetinește, stă;
  - muzică: 90-110 BPM (smooth, cool) sau 115-123 BPM (elite, kinetic);
  - sound design minimal: dacă un sunet nu ajută, scoate-l.
- Conținutul (propunere, o rafinezi):
  1. "2 milioane de contoare. 192 de milioane de citiri pe zi." (cifrele PPC)
  2. "Un scor de 0,87 nu îi spune unui tehnician unde să meargă mâine." (citat din tema PPC)
  3. Apare numele produsului.
  4. Cele trei semnale: contoare, furtună, tensiune.
  5. Perceive → Estimate → Decide → Act.
  6. Harta cu traseele echipelor (captură reală din interfață, după ora 01:00).
  7. "Nu sunt sigur" → un om decide.
  8. Cifra principală față de baseline, DOAR din `reports/` (altfel cadrul rămâne fără cifră).
  9. Final: CyberPunks · SmartHack XI 2026 · tema PPC.
- Imagini: Codex (modelul de imagine "image 2.6") prin `delegate_task` către `codex`, pentru fundaluri sau obiecte stilizate (contor, stâlp, transformator), salvate în `presentation/assets/`. Creditele spun ce e generat cu AI.
- Muzică: originală (sintetizată local) sau cu licență liberă clară (CC0), citată în `presentation/CREDITS.md`. Fără voce, sau voce locală (Kokoro), opțional.
- Export: 1920×1080, H.264 High, yuv420p, AAC 48 kHz, loudnorm −16 LUFS / −1 dBTP, `+faststart`. Opțional o variantă verticală 1080×1920.
- Review: după primul export, două review-uri independente (vizual pe Claude, tehnic pe Codex), ca la filmul NextMove (`~/Documents/LLM-Wiki/wiki/patterns/ai/pitch-film-from-app-recordings.md`). Repară ce găsesc.
- Etape: 15:00 storyboard cu cadre statice, arătat lui Teo cu `html_render`; 19:00 v0 animat pe cadrele statice; 02:00 v1 cu capturi reale din interfață; 08:00 final.

## Slideuri și scriptul demo-ului

- Demo live: 5 minute, apoi 2 minute de întrebări tehnice. Scrie `presentation/demo-script.md` cu replicile pe secunde, ce se arată, cine vorbește și planul B dacă pică ceva.
- Slideuri (HTML exportat în PDF sau alt format bun pe proiector): problema cu cifrele PPC, produsul, Perceive/Estimate/Decide/Act, cele trei modele cu metricile față de baseline (cifre reale din `reports/`), robustețea și "nu sunt sigur", explicabilitatea, etica și EU AI Act, costuri și scalare pe platforma lor (S3, Spark, NiFi), ce urmează. Cifrele le iei din `reports/` după 21:30 și verifici fiecare cifră înainte de final.
- Înregistrarea de rezervă a demo-ului: captură video a interfeței reale, 4-5 minute, după ora 03:00.
- Exporturile finale (MP4 sub 50 MB, PDF) intră în git în `presentation/exports/`; fișierele temporare nu.

## Milestones (ora României)

- 14:30 M0: HyperFrames instalat și un test de 2 secunde randat, regulile stilului notate, primele schițe.
- 15:00 storyboard arătat lui Teo.
- 19:00 v0 animat.
- 02:00 v1 cu capturi reale.
- 03:00 scriptul demo-ului și slideurile v1.
- 08:00 video final, slideuri finale, înregistrarea de rezervă.
