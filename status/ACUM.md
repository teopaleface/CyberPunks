# Ce se face acum (instantaneu scris de orchestrator)

Actualizat: 2026-11-07 13:39. Detalii pe fiecare fir: `status/<branch>.md`. Planul: `docs/PLAN.md`. Contextul și deciziile: `memory/` (jurnalul cu ore: `memory/journal.md`).

## Produsul

"Tura de mâine": agentul care decide unde merg mâine echipele de teren Rețele Electrice, pe baza modelelor noastre (A contoare, B furtună, C tensiune la posturi cu prosumatori, plus bilanțul pe post), cu decizii explicate și "nu sunt sigur" trimis la om. Ziua demo: 8 iulie 2025 (caniculă în București-Ilfov, vijelii cu cod roșu în Banat).

## Integrat în `Teo` acum

- Primul rulaj cap-coadă cu modele reale (`uv run cyberpunks run --scenario demo-vara`): A 249 de lucrări valide, B 26, C încă lipsă (vine la M1). Agentul: 33 de lucrări în trasee pentru 9 echipe (378 km), 152 de citiri la distanță, 65 trimise la om, 25 amânate, 0 în carantină, OR-Tools în 6 s. Cifre provizorii.
- Testele: 138 trec (`make check`).

## Pe fire

| Fir | Unde e | Ce urmează |
|---|---|---|
| A contoare | M1 gata (SGCC și Londra, baseline-uri, LightGBM, lucrări valide) | M2: features față de vecini, ceas decalat, derivă, analiza erorilor |
| B furtună | M1 provizoriu (19 din 80 de comitate), integrat | ~15:15 M1 final pe 80 de comitate; M2: cuantile cu acoperire corectă |
| C prosumatori | M0 (calcul de rețea de ~30.000 de ori mai rapid decât pandapower, verificat) | M1 17:30: modelul, lucrările, registrul comun de posturi; apoi scara de soluții |
| Bilanț pe post | M0, cercetare (pornit după decizia lui Teo) | M1 17:30: lumea simulată, modelul pierderii normale |
| Planificator | M1 gata, M2 în lucru (ordine de lucru PDF gata) | evaluarea agentului pe 30 de zile, acțiunile noi, scara C, fuziunea cu bilanțul |
| Interfață | M0 (direcția "Panou", logo, Next.js) | M1 17:30: harta, linia de timp a echipelor, coada "Nu sunt sigur", detaliul lucrării |
| Prezentare | M0 (HyperFrames merge, storyboard, imagini Codex, harta NASA) | storyboard pentru Teo, v0 animat cu muzică la 19:00 |

## Decizii recente (vezi `memory/journal.md`)

- A, B, C în paralel, cu orchestrator.
- Bilanț pe post (fir nou) și scara de soluții pentru tensiune, cu mesaje țintite pe post și baterii calculate pe profil.
- Research "probleme reale PPC 2026" ca sursă de lucru (neverificat): `memory/12-probleme-reale-ppc-2026.md`.
- De lămurit: pragurile de repunere în funcțiune (8/12/48 h în document, 4/6/12 h în Ord. ANRE 46/2021).

## Termene

M1 17:30 · M2 21:30 · integrarea 22:00 · M3 03:00 · M4 08:00 · înghețare 10:30 · predare duminică 12:00 · demo 13:00. Regula de la 21:30: un model care nu bate metoda simplă primește efortul întâi.
