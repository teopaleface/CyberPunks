---
format: 1920x1080
duration: 30s
message: "Un scor nu trimite pe nimeni la teren. Tura de mâine face planul echipelor și întreabă un om când nu e sigură."
arc: Noaptea (scara) → Problema (0,87) → Numele → Semnalele → Agentul (Perceive, Estimate, Decide, Act) → Omul → Dovada → Dimineața
audience: juriul PPC la SmartHack XI 2026 (oameni de date și de rețea de la Rețele Electrice și PPC)
music: originală, 96 BPM, 12 măsuri de 2,5 s; schimbările de cadru cad pe măsuri
---

Regulile de stil: `../STYLE.md`. Fiecare cadru are o singură idee. Cifrele PPC vin din `memory/08-ppc-workshop-ai.md`; cifra noastră (cadrul 7) vine doar din `reports/`.

## Frame 1 — Noaptea (0-5s)

- act: Problema
- scene: România noaptea, din satelit (imagine reală NASA). Cele trei regiuni Rețele Electrice rămân luminate, restul se stinge. Camera împinge lent.
- duration: 5s
- transition_in: cut (primul cadru are deja harta pe ecran, la 55%)
- reads: "2 milioane de contoare inteligente." (0,3-2,3 s); "192 de milioane de citiri pe zi." (2,4-4,8 s)
- sound: pad cald care urcă din liniște; ping-uri rare, apoi un fir de date în șaisprezecimi
- status: built
- src: compositions/s1-noapte.html

Scara problemei, cu cifrele spuse de PPC la workshop. Zoom prin lumina Bucureștiului spre cadrul 2.

## Frame 2 — Scorul (5-10s)

- act: Problema
- scene: Lumina se strânge și din ea iese scorul "0,87". Sub el, fraza din tema PPC.
- duration: 5s
- transition_in: zoom printr-o lumină
- reads: "0,87, scor de anomalie" (5,0-6,2 s); "nu îi spune unui tehnician unde să meargă mâine dimineață." (6,25-9,7 s); "Din tema PPC" (7,0-9,7 s)
- sound: firul de date se oprește la 5,0; o notă joasă și o notă de pian; ultima jumătate de bătaie e o respirație
- status: built
- src: compositions/s2-scor.html

Citatul PPC, aproape cuvânt cu cuvânt. Scorul se strânge într-un punct.

## Frame 3 — Numele (10-12,5s)

- act: Răspunsul
- scene: Punctul în care s-a strâns scorul devine prima oprire a traseului din logo. Traseul se desenează, soarele răsare în spatele lui, apoi semnul se așază lângă nume, ca în antetul consolei.
- duration: 2.5s
- transition_in: obiectul devine lumea (scorul → prima oprire → logoul → numele)
- reads: "Tura de mâine" (10,7-12,3 s); "Planifică echipele de teren." (10,9-12,3 s)
- sound: pe 10,0 armonia se deschide, intră toba mare și basul
- status: built
- src: compositions/s3-nume.html

## Frame 4 — Semnalele (12,5-16,25s)

- act: Răspunsul
- scene: Ziua reală a demo-ului, marți, 8 iulie 2025. Trei lumi, câte una pe 1,25 s: contorul, furtuna, panourile solare. Fiecare are markerul sursei din consolă (A, B, C) și e un model antrenat de noi.
- duration: 3.75s
- transition_in: whip
- reads: "Marți, 8 iulie 2025" (12,55-16,1 s); "Contoare suspecte." (12,6-13,75 s); "Vijelie în Banat." (13,85-15,0 s); "Tensiune peste limită." (15,1-16,1 s)
- sound: groove-ul pornește: tobă pe 1 și 3, rim pe 2 și 4
- status: built
- src: compositions/s4-semnale.html

Imaginile sunt generate cu Codex și au eticheta "Imagine generată cu AI".

## Frame 5 — Agentul (16,25-22,5s)

- act: Agentul
- scene: Harta București-Ilfov. Perceive: lucrările apar. Estimate: fiecare primește mărimea scorului. Decide: ce e sigur primește echipă, ce nu e sigur merge "la om", restul se amână; camera intră pe contorul cel mai sigur, iar bilanțul postului lui (energia ieșită din post față de cea facturată) confirmă suspiciunea, deci deplasarea nu e degeaba. Act: traseele echipelor se desenează din bazele operative.
- duration: 6.25s
- transition_in: blur pe aceeași scenă
- reads: "Aceleași echipe, un singur plan." (16,4-18,7 s); "Perceive" (16,25), "Estimate" (17,5), "Decide" (18,75), "Bilanțul confirmă." (19,05-19,9 s), "Act" (20,0), apoi traseele până la 22,3 s
- sound: groove plin, câte o notă pe fiecare pas; cea mai caldă parte a piesei
- status: built (schiță cu date sintetice; se înlocuiește cu captura din consolă după 01:00)
- src: compositions/s5-agent.html

## Frame 6 — Omul (22,5-25s)

- act: Încrederea
- scene: Stâlpul cu transformator în ploaie, întunecat. "Nu sunt sigur." apoi "Un om decide."
- duration: 2.5s
- transition_in: blur
- reads: "Nu sunt sigur." (22,6-24,8 s); "Un om decide." (23,5-24,8 s)
- sound: tobele tac; pad și un acord ținut
- status: built (după 01:00: cardul real de revizuire din consolă)
- src: compositions/s6-om.html

## Frame 7 — Dovada (25-27,5s)

- act: Încrederea
- scene: Cifra noastră față de baseline, cu două bare.
- duration: 2.5s
- transition_in: blur
- reads: cifra (25,1-27,3 s); ce măsoară (25,3-27,3 s)
- sound: tobele revin, mai ușor
- status: outline (cifra vine din reports/ după 21:30; fără cifră, cadrul rămâne fără cifră)
- src: compositions/s7-cifra.html

## Frame 8 — Dimineața (27,5-30s)

- act: Final
- scene: Noaptea se face dimineață: câmpia la primele lumini, stâlpi la orizont. Logoul și numele, iar soarele din logo răsare odată cu zorii; apoi echipa.
- duration: 2.5s
- transition_in: inundație de culoare
- reads: "Tura de mâine" (27,6-30 s); "CyberPunks" și "SmartHack XI 2026, tema PPC" (27,9-30 s)
- sound: acord major de rezolvare exact pe 27,5, apoi coada de reverb până la liniște
- status: built
- src: compositions/s8-final.html
