# Muzica filmului „Tura de mâine”

Trei variante, toate compuse în cod de echipă, fără sample-uri:

- **Varianta 3, 36 s** (cea nouă, pentru scenariul nou, mai simplu): `compose_v3.py`. E prima secțiune de mai jos.
- **Varianta cinetică, 120 BPM, 30 s** (filmul pe alb): `compose_kinetic.py`. Rămâne în repo, cu fișierele ei.
- **Varianta calmă, 96 BPM** (prima, „de la noapte la zori”): `compose.py`. Rămâne în repo, cu fișierele ei; secțiunea ei e la final.

## Varianta 3: 36 s, scenariul nou (120 BPM)

Scenariul nou e mai simplu: furtuna din 8 iulie 2025 din Banat, întrebarea „Dar unde?”, trei probleme, răspunsul („Tura de mâine face planul.”), produsul, omul care aprobă, apoi finalul pe negru, cu logoul. Muzica păstrează sunetele variantei cinetice (aceleași instrumente, același mixaj, aceleași verificări). Se schimbă forma piesei și harta loviturilor.

- **36,000 s**, 120 BPM, 4/4, 18 măsuri de 2,0 s. O bătaie = 0,5 s = **exact 15 cadre** la 30 fps; o măsură = 60 de cadre. Toate loviturile din imagine cad pe cadre întregi.
- Tonalitatea: la major. Cârligul stă în fa diez minor, peste un fa diez ținut în bas, așa că sună întunecat și încordat. Pe „Tura de mâine face planul.” (12,0) muzica trece în la major.
- Codul: `compose_v3.py` (muzica) și `analyze_v3.py` (verificările). Instrumentele vin din `compose_kinetic.py`, uneltele din `compose.py`. Amândouă rămân neschimbate: `compose_kinetic.py` dă aceiași octeți ca înainte.
- Sunete noi, tot sintetizate în cod: un tunet îndepărtat pe 1,0 (zgomot filtrat sub 240 Hz, care se rostogolește), un tom acordat pe treptele problemelor, o notă joasă care crește încet sub padul întunecat. Fără sample-uri și fără biblioteci de efecte.

### Cum o refaci

Din rădăcina repo-ului:

```bash
uv run python presentation/music/compose_v3.py
```

Durează cam 30 de secunde: randează de două ori (ca să verifice că iese identic), scrie tot în `presentation/music/out/`, rulează verificările (`analyze_v3.py`), desenează graficele și face copia de ascultat (mp4).

Opțiuni: `--out DOSAR`, `--no-m4a`, `--no-analyze` (fără verificări, grafice și mp4), `--no-determinism` (o singură randare).

Doar verificările, pe fișierele existente: `uv run python presentation/music/analyze_v3.py`.

### Fișierele (în `out/`)

| Fișier | Ce e |
|---|---|
| `tura_v3_36s.wav` | mixajul: 48 kHz, 24 de biți, stereo, exact 1.728.000 de eșantioane (36,000 s) |
| `tura_v3_36s.m4a` | previzualizare AAC 256 kbps; pentru montaj folosiți WAV-ul |
| `tura_v3_36s_asculta.mp4` | **copia de ascultat**: graficul formei de undă, cu o linie albă care arată unde a ajuns muzica, plus sunetul. H.264 + AAC, exact 36,0 s (1080 de cadre) |
| `stems_v3/` | `drums`, `bass`, `pad`, `stabs`, `lead`, `fx`; adunate dau exact mixajul (0 LSB diferență) |
| `cues_v3.json` | măsurile, cele 72 de bătăi cu cadrul lor, acordurile, cele 25 de lovituri (nume, timp, cadru, ce cântă, stem-ul), fereastra de aer și toate evenimentele (kick, clap, snare, stab, motiv, arpegiu, bas, risere) |
| `waveform_v3.png`, `spectrogram_v3.png` | graficele, cu liniile de măsură și loviturile filmului |
| `report_v3.json` | toate măsurătorile; la `checks`, fiecare cerință cu „trece” sau „nu trece” |

În git intră m4a-ul, mp4-ul, `cues_v3.json`, graficele și raportul. WAV-urile și `stems_v3/` se refac identic din cod (vezi `presentation/.gitignore`).

### Forma piesei

| Măsurile | Timp (s) | Cadre | Ce se întâmplă | Acorduri |
|---|---|---|---|---|
| 1-2 | 0-4 | 0-120 | **Cârligul**, întunecat și rar. 0,0: un acord jos și moale. 1,0: boom acordat pe fa diez, acord întunecat și tunet îndepărtat. 2,0: lovitura grea, cu un sub care coboară o octavă (curentul se duce). Apoi pad întunecat până la 4,0, fără tobe | F#m, D/F#, Bm/F# (toate peste fa diez în bas) |
| 3-4 | 4-8 | 120-240 | **Întrebarea**. 4,0: intră un puls ușor (kick moale pe 1 și 3, hi-hat, bas ușor). 6,0: totul tace, cu tot cu reverb; rămâne doar un acord suspendat, încet, până la 7,75. Pe 7,75 și 7,875: două lovituri mici de snare spre 8,0 | Dmaj9; apoi mi suspendat cu nonă (mi, la, si, fa diez), lăsat fără răspuns |
| 5-6 | 8-12 | 240-360 | **Problemele**: trei lovituri (8,0, 9,0, 10,0), fiecare cu o treaptă mai sus, și în acorduri, și în tom. Kick pe 1 și 3, bas în optimi. 11,0-12,0: riser și rafală de snare | Bm11, C#m7, Dmaj7#11 (aceeași formă în cvarte, urcată), Esus4, E |
| 7-12 | 12-23 | 360-690 | **Răspunsul și produsul**: pe 12,0 vine la major și pornește groove-ul (kick pe fiecare timp, clap pe 2 și 4). 15,0 consola, 16,0 clicul, motivul de 4 note pe 16,5-18,0, accent pe 18,0, apoi arpegiul. Umplutură ușoară pe 22,0 | A, E/G# (14,0), F#m9 (15,0), Dmaj9 (16,0), A (18,0), E/G#, F#m9, Dmaj9, Esus4 (22,0), E |
| 12-14 | 23-27 | 690-810 | **Omul**: pe 23,0 tobele ies și padul se închide; pe 25,0 o notă moale pentru card; pe 26,0 clicul pe „Aprobă” și tobele revin | F#m9 (23,0), Bm11 (25,0), Dmaj9 (26,0) |
| 14-15 | 27-29 | 810-870 | **Build**, cu măsură: snare în optimi, apoi în șaisprezecimi, riser, basul se subțiază; ultima șaisprezecime e goală | Esus4, E (28,0) |
| 15-16 | 29-32 | 870-960 | **Drop**, pe negru: lovitura mare pe 29,0, accent pe 30,0 | A (29,0), Dmaj9 (30,0), Esus4, E |
| 17-18 | 32-36 | 960-1080 | **Logoul**: A add9, tobele se opresc, coada se stinge; zero digital de la 35,9 | A add9 |

De ce așa:

- **Întrebarea primește răspuns.** „Dar unde?” cade pe mi suspendat (dominanta), lăsat în aer. Riserul de dinainte de 12,0 se întoarce pe mi și de data asta se rezolvă în la major, fix pe „Tura de mâine face planul.”.
- **Problemele urcă o treaptă pe lovitură** (si, do diez, re, apoi mi în riser), cu aceeași formă de acord în cvarte. Tom-ul cântă aceeași fundamentală, ca treptele să se audă și în tobe.
- **„Când nu e sigur”** cade pe fa diez minor după mi: urechea așteaptă la și primește altceva (cadență întreruptă). „Aprobă” aduce re major, apoi build pe mi și drop pe la.
- **Finalul e IV, V, I** (Dmaj9 pe 30,0, mi, apoi A add9 pe 32,0): urechea ajunge acasă exact pe logo.
- **Motivul echipelor** e cel din varianta cinetică: si, do diez, mi, la, câte o notă pe 16,5, 17,0, 17,5 și 18,0. Ultima notă, tonica, cade pe „Fiecare echipă știe unde merge.”.

### Loviturile filmului (măsurate)

Eroarea = atacul găsit de detector minus momentul cerut, în milisecunde. „Mixaj” = în piesa întreagă; „stem” = doar în stem-ul care poartă lovitura. Detectorul are pasul de 1 ms; întârzierea lui, măsurată pe clicuri sintetice, e scăzută. Un cadru are 33,3 ms; cerința e ±10 ms.

| Timp (s) | Cadrul | Pe ecran | Ce cântă | Eroare mixaj (ms) | Eroare stem (ms) |
|---|---|---|---|---|---|
| 0,0 | 0 | „8 iulie 2025.” | acord jos și moale (fa diez minor) + bas fa diez + kick foarte moale | 0,25 | 0,25 (stabs) |
| 1,0 | 30 | „Vijelie în Banat.” (norul de furtună 3D intră) | acord întunecat (re peste fa diez) + boom acordat pe fa diez + tunet îndepărtat (zgomot sintetizat) | 0,25 | 1,25 (stabs) |
| 2,0 | 60 | „Zeci de mii de case fără curent.” (apoi pad întunecat până la 4,0) | acord greu (si minor peste fa diez) + kick + boom + clap + crash + sub care coboară o octavă | 0,25 | 2,25 (stabs) |
| 4,0 | 120 | „Mâine dimineață pleacă echipele.” (casca intră) | acord scurt (Dmaj9) + hi-hat; pulsul: kick moale pe 1 și 3, hi-hat pe contratimp, bas ușor | 1,25 | 2,25 (stabs) |
| 6,0 | 180 | „Dar unde?” (totul tace, rămâne un acord suspendat) | acordul suspendat (mi, la, si, fa diez), singur; tot restul tace până la 7,75 | 2,25 | 2,25 (stabs) |
| 7,75 | 232,5 (muzical) | două lovituri mici de snare spre 8,0 | două lovituri mici de snare (7,75 și 7,875) | 0,25 | 0,25 (drums) |
| 8,0 | 240 | „Stâlpi căzuți.” (stâlpul 3D) | acord în cvarte + kick + tom acordat pe fundamentală (si, do diez, re: câte o treaptă mai sus) | 0,25 | 1,25 (stabs) |
| 9,0 | 270 | „Curent furat.” (al doilea obiect 3D) | acord în cvarte + kick + tom acordat pe fundamentală (si, do diez, re: câte o treaptă mai sus) | 0,25 | 1,25 (stabs) |
| 10,0 | 300 | „Prea mult soare.” (panoul solar) | acord în cvarte + kick + tom acordat pe fundamentală (si, do diez, re: câte o treaptă mai sus) | 1,25 | 1,25 (stabs) |
| 11,0 | 330 | riser și rafală de snare spre 12,0 | rafală de snare (optimi, apoi șaisprezecimi) + riser din zgomot + riser tonal | 1,25 | 1,25 (drums) |
| 12,0 | 360 | „Tura de mâine face planul.” (soarele logoului răsare) | la major mare + kick + boom + clap + crash + trei clopoței; groove-ul pornește | 2,25 | 1,25 (stabs) |
| 15,0 | 450 | consola apare | acord mare + kick + clap + crash mic | 1,25 | 1,25 (stabs) |
| 16,0 | 480 | CLIC pe „Rulează agentul” | acord foarte scurt + clap strâns (clicul) | 1,25 | 1,25 (stabs) |
| 16,5 | 495 | traseele echipelor se desenează (1/4) | o notă din motiv (coardă ciupită + clopoțel) | 1,25 | 1,25 (lead) |
| 17,0 | 510 | traseele (2/4) | o notă din motiv (coardă ciupită + clopoțel) | 2,25 | 2,25 (lead) |
| 17,5 | 525 | traseele (3/4) | o notă din motiv (coardă ciupită + clopoțel) | 1,25 | 1,25 (lead) |
| 18,0 | 540 | „Fiecare echipă știe unde merge.” (4/4) | ultima notă a motivului (la) + acord mare + kick + clap + crash | 1,25 | 1,25 (lead) |
| 22,0 | 660 | umplutură ușoară spre 23,0 | umplutură ușoară de snare (optimi, apoi șaisprezecimi) + hi-hat deschis | 1,25 | 1,25 (drums) |
| 23,0 | 690 | „Când nu e sigur, întreabă dispecerul.” (tobele ies) | acord moale și filtrat (F#m9); tobele ies până la 26,0 | 3,25 | 1,25 (stabs) |
| 25,0 | 750 | cardul real apare | o notă moale (fa diez) din motiv | 2,25 | 1,25 (lead) |
| 26,0 | 780 | CLIC pe „Aprobă” (tobele revin) | acord + kick + clap + crash; tobele revin | 0,25 | 1,25 (stabs) |
| 27,0 | 810 | build: rafală de snare și riser spre 29,0 | rafală de snare (optimi, apoi șaisprezecimi) + riser din zgomot + riser tonal | 1,25 | 1,25 (drums) |
| 29,0 | 870 | pastila neagră umple ecranul: „Aceleași echipe.” | la major mare + kick + boom + clap + crash | 1,25 | 1,25 (stabs) |
| 30,0 | 900 | „Aproape cu jumătate mai mult câștig.” | acord mare + kick + clap + crash mic | 1,25 | 1,25 (stabs) |
| 32,0 | 960 | logoul: soarele răsare peste traseu | A add9 mare + kick + boom + crash + clopoței; tobele se opresc | 2,25 | 1,25 (stabs) |

Toate 25 din 25 se regăsesc, toate la ±10 ms. Mediana erorii absolute: **1,25 ms** în mixaj (maxim 3,25 ms) și 1,25 ms în stem-uri (maxim 2,25 ms), adică sub o zecime de cadru. Pickup-ul de pe 7,75 e o șaisprezecime muzicală, la cadrul 232,5. Nu e o lovitură din imagine, așa că nu l-am mutat pe un cadru întreg (ar fi ieșit de pe grilă cu 17 ms).

### Verificări (măsurate, nu ascultate)

| Ce | Rezultat |
|---|---|
| Durata | 1.728.000 de eșantioane = 36,000000 s, 48 kHz, 24 de biți, stereo |
| Loudness integrat | -16,0 LUFS (ffmpeg ebur128); calcul propriu BS.1770 -16,00; loudnorm -16,18 |
| Vârf real (true peak) | -1,3 dBTP (ffmpeg), 0 eșantioane tăiate. Limitatorul lucrează doar pe loviturile mari: 2,0 (1,6 dB), 12,0 (1,56 dB), 29,0 (1,35 dB), câte ~0,3 s; sub 0,5 dB pe 10,1 și 26,0 |
| Plaja de loudness (LRA) | 6,3 LU (mai mare decât în varianta cinetică: aerul și momentul uman sunt intenționat încete) |
| Pe secțiuni (LUFS, fără porți) | cârlig 0-4: -17,3; puls 4-6: -20,1; aer 6-7,75: -33,2; probleme 8-12: -15,9; răspuns 12-15: -15,0; produs 15-23: -15,2; uman 23-26: -20,5; Aprobă 26-27: -14,3; build 27-29: -15,6; drop 29-32: -14,4; final 32-35,9: -17,1 |
| Aerul de la „Dar unde?” (6,0-7,75) | -35,8 dBFS RMS / -33,2 LUFS pe toată fereastra, cu tot cu atacul acordului. Față de loviturile din cârlig (primele 300 ms): **cu 17,1 dB sub cea mai moale** (0,0), 19,7 dB sub 1,0 și 20,7 dB sub 2,0 (în LUFS; în RMS: 19,0, 22,3 și 22,6 dB). În fereastră, celelalte stem-uri sunt zero digital |
| Tobele pe 23,0-26,0 | zero digital (stem-ul `drums`) |
| Ultimele 100 ms | zero digital |
| Suma stem-urilor | identică cu mixajul (0 LSB diferență) |
| Tempo | 120,0 BPM (autocorelația atacurilor din groove, 12-23 s) |
| Pe grilă | tobele: 149 din 149 atacuri la ±10 ms de grila de 32-imi; mixajul: 156 din 157 (excepția e o notă de bas de pe 8,5, detectată cu 15 ms mai târziu) |
| Spectru, 2-6 kHz | fără vârfuri: cea mai mare bandă de 1/3 de octavă iese cu 0,9 dB peste vecine în groove, 1,4 dB în drop și 1,0 dB pe toată piesa (limita: 3 dB); banda 2-6 kHz e cu 11,8 dB sub 300 Hz-2 kHz |
| Zona joasă | sub 120 Hz totul e mono (canalul lateral e cu 35,7 dB sub cel central); 125-250 Hz e cu 3,3 dB peste 500 Hz-1 kHz (cald, nu „bubuie”) |
| Mono | corelație L/R 0,96; în mono piesa e doar cu 0,2 dB mai încet |
| Determinism | două randări dau aceiași octeți, pe 9 fișiere (WAV, cele 6 stem-uri, cues, m4a) |
| Copia de ascultat | mp4 de 36,000 s: 1080 de cadre H.264 (1920×662), AAC de 36,000 s |

### Pentru montaj

- Puneți WAV-ul la cadrul 0. O bătaie = 15 cadre, o măsură = 60 de cadre: nu e nevoie de rotunjiri.
- Loviturile sunt fix pe cadru, fără umanizare. Lista completă, cu cadrul fiecăreia: `cues_v3.json`, cheia `hits`. Pickup-ul de pe 7,75 are acolo `picture_hit: false`.
- Între 6,0 și 7,75 muzica e aproape mută: dacă în imagine e liniște, e liniște și în sunet.
- Stab-urile și motivul au un ecou discret de 3/16 (0,375 s, tot pe grilă). Dacă încurcă, coborâți stem-urile `stabs` și `lead`.
- Ce se schimbă ușor (în `compose_v3.py`, sus): `HITS` (loviturile și notele lor), `TIMELINE` (acordurile), `MIX_DB` (nivelurile), `PAD_LEVEL` și `PAD_CUTOFF` (padul). Loudness-ul final se reface singur la -16 LUFS.

### Ce trebuie ascultat de un om

Cifrele de mai sus nu spun cum sună. De ascultat o dată în căști și o dată pe difuzoarele din sală (sau ale laptopului), cu `tura_v3_36s_asculta.mp4`:

- dacă aerul de la 6,0-7,75 se mai aude în sală: acordul suspendat e la -33 LUFS. Dacă dispare, urcați-i velocity-ul (în `compose_v3.py`, la tipul `sus`: primul număr din `stab(...)`, acum 0,2). Până la 0,25 (+2 dB) aerul rămâne cel puțin 15 dB sub cârlig; peste, nu mai trece verificarea;
- dacă tunetul de pe 1,0 se aude ca furtună și nu ca zgomot (e ținut mic, sub boom; nivelul lui e `MIX_DB["rumble"]`);
- dacă pulsul de la 4,0 (-20 LUFS) e destul de prezent pentru „Mâine dimineață pleacă echipele.”;
- dacă acordul de pe 6,0 (mi suspendat cu nonă) sună a întrebare;
- dacă tobele care ies pe 23,0 (în 50 ms) sună intenționat sau prea brusc;
- dacă build-ul 27-29 e de bun gust, nu „EDM de festival”;
- lovitura finală (32,0) e cu ~1 dB mai tare decât drop-ul (29,0), ca vârf de moment: de verificat că finalul nu pare că „sare”;
- pe difuzoare mici, boom-ul și basul din cârlig (46 Hz) se aud mai slab; armonicele lor ar trebui să le facă totuși simțite.

### Licență

Muzică originală compusă în cod de echipa CyberPunks pentru acest proiect, fără sample-uri. Publicată sub CC0 1.0 (domeniu public): oricine o poate folosi, fără nicio condiție.

*Original music composed in code by the CyberPunks team for this project, no samples. Released under CC0 1.0.*

## Varianta cinetică: 120 BPM

Filmul nou ia gramatica unui film rapid de lansare: fundal alb, cuvinte uriașe care se schimbă pe bătăi, obiecte 3D care intră în cadru, butoane apăsate la scară mare, apoi un final închis la culoare, cu logoul. Muzica e pe măsură: pop/house electronic, curat și sigur pe el. Nu e EDM de festival, nici trap, fără voce.

- **30,000 s**, 120 BPM, 4/4, 15 măsuri a câte 2,0 s. O bătaie = 0,5 s = **exact 15 cadre** la 30 fps; o măsură = 60 de cadre. Toate loviturile cad pe cadre întregi.
- Tonalitatea: la major. Începe pe fa diez minor (problema) și se termină pe la major (logoul).
- Totul e sintetizat în Python (numpy și scipy): kick acordat pe la (55 Hz), clap și snare din zgomot filtrat, hi-hat din zgomot și oscilatoare „metalice”, bas din fierăstrău filtrat, pad din cinci fierăstraie dezacordate care pompează pe kick (sidechain), acorduri scurte („stab”) din fierăstraie cu un filtru care se închide repede, motivul pe o coardă ciupită Karplus-Strong, un arpegiu, risere din zgomot și glissando.
- Din `compose.py` refolosim doar unelte (reverb, ecou, limitator, loudness, coarda ciupită, scrierea WAV). `compose.py` și fișierele lui nu se schimbă.
- Fără sample-uri, loop-uri sau soundfont-uri. Seed fix: două randări dau aceiași octeți (se verifică la fiecare rulare).

### Cum o refaci

Din rădăcina repo-ului:

```bash
uv run python presentation/music/compose_kinetic.py
```

Durează cam 22 de secunde: randează de două ori (ca să verifice că iese identic), scrie tot în `presentation/music/out/` și rulează verificările (`analyze_kinetic.py`).

Opțiuni: `--out DOSAR` (alt dosar), `--no-m4a`, `--no-analyze`, `--no-determinism` (o singură randare, cam 8 secunde).

Doar verificările, pe fișierele existente: `uv run python presentation/music/analyze_kinetic.py`.

### Fișierele (în `out/`)

| Fișier | Ce e |
|---|---|
| `tura_120bpm_30s.wav` | mixajul: 48 kHz, 24 de biți, stereo, exact 1.440.000 de eșantioane (30,000 s) |
| `tura_120bpm_30s.m4a` | previzualizare AAC 256 kbps; pentru montaj folosiți WAV-ul |
| `stems_120/` | `drums`, `bass`, `pad`, `stabs`, `lead`, `fx`; adunate dau exact mixajul (0 LSB diferență) |
| `cues_120.json` | măsurile, cele 60 de bătăi cu cadrul lor, acordurile, cele 23 de lovituri (nume, timp, cadru, ce cântă) și toate evenimentele (kick, clap, stab, motiv, arpegiu, bas, risere) |
| `spectrogram_120.png`, `waveform_120.png` | graficele, cu liniile de măsură și loviturile filmului |
| `report_120.json` | toate măsurătorile de mai jos |

În git intră m4a-ul, `cues_120.json`, graficele și raportul. WAV-urile și `stems_120/` se refac identic din cod (vezi `presentation/.gitignore`).

### Forma piesei

| Măsurile | Timp (s) | Cadre | Ce se întâmplă | Acorduri |
|---|---|---|---|---|
| 1-3 | 0-6 | 0-180 | Cârligul, pe alb: câte un acord scurt pe fiecare cuvânt, fără kick continuu. După „un plan.” (2,0) e aer până la 3,0. Acordul de pe 4,5 ține până la 6,0, cu un riser în ultima jumătate de măsură | F#m9, E/G#, Dmaj9; apoi Bm11, C#m7, Dmaj7#11 (aceeași formă în cvarte, mutată în sus pe gamă), Esus4 |
| 4-10 | 6-20 | 180-600 | Produsul: kick pe fiecare timp, clap pe 2 și 4, hi-hat, bas care se rostogolește, pad care pompează. Din 12,0 intră arpegiul și hi-hat-ul deschis. 17,5-19,0: energia scade (filtrul se închide, tobele se rup); pe 19,0 revine tot | A, E/G#, F#m9, Dmaj9, A/C# (împins pe 13,5), E (împins pe 15,5), F#m9 (17,5), Dmaj9 (19,0) |
| 11 | 20-22 | 600-660 | Build: rafală de snare (optimi, șaisprezecimi, apoi 32-imi), hi-hat tot mai tare, riser, basul se subțiază, filtrul padului se deschide; totul se oprește fix pe 22,0 | Esus4 → E |
| 12-13 | 22-26 | 660-780 | Drop, pe negru: lovitură mare, apoi tot energic, dar mai rar (fără hi-hat închis, bas pe contratimp). Arpegiul urcă 12 note exact cât urcă cifra (22,0-23,5) | A, Dmaj9 (24,0), Esus4 (25,0), E (25,5) |
| 14-15 | 26-30 | 780-900 | Logoul: A add9 mare, tobele se opresc, coada se stinge; zero digital de la 29,9 | A add9 |

De ce așa:

- **Finalul e IV - V - I** (Dmaj9, E, A add9): urechea ajunge acasă exact pe logo.
- **„Nu sunt sigur”** cade pe fa diez minor, **„Aprobă”** pe re major (mai luminos), apoi build pe mi și drop pe la.
- **Motivul agentului**: si, do diez, mi, la (B4, C#5, E5, A5), câte o notă pe Perceive, Estimate, Decide, Act. Urcă cu pași tot mai mari; ultima notă e chiar tonica.
- **Cârligul** urcă pe aceeași formă de acord (în cvarte) pe si, do diez, re, mi: fiecare obiect 3D primește un acord cu un pas mai sus.

### Loviturile filmului (măsurate)

Eroarea = atacul găsit de detector minus momentul cerut, în milisecunde. „Mixaj” = în piesa întreagă; „stem” = doar în stem-ul care poartă lovitura (`stabs` sau `lead`). Detectorul are pasul de 1 ms; întârzierea lui, măsurată pe clicuri sintetice, e scăzută. Un cadru are 33,3 ms.

| Timp (s) | Cadrul | Pe ecran | Ce cântă | Eroare mixaj (ms) | Eroare stem (ms) |
|---|---|---|---|---|---|
| 0,0 | 0 | „Un scor” | stab + kick scurt + bas | 0,25 | 1,25 (stabs) |
| 0,5 | 15 | „de 0,87” | stab + kick scurt + bas | 1,25 | 2,25 (stabs) |
| 1,5 | 45 | „nu e” | stab + kick scurt + bas | 1,25 | 2,25 (stabs) |
| 2,0 | 60 | „un plan.” (apoi aer până la 3,0) | stab mare + kick + clap (+ crash în groove) | 0,25 | 2,25 (stabs) |
| 3,0 | 90 | „Contoare.” (contorul 3D intră) | stab + kick scurt + bas | 1,25 | 2,25 (stabs) |
| 3,5 | 105 | „Furtuni.” (norul de furtună) | stab + kick scurt + bas | 1,25 | 1,25 (stabs) |
| 4,0 | 120 | „Tensiune.” (panoul solar) | stab + kick scurt + bas | 1,25 | 1,25 (stabs) |
| 4,5 | 135 | „Aceleași echipe.” (cele patru obiecte) | acord ținut + kick + clap + crash mic; riser 5,0-6,0 | 1,25 | 2,25 (stabs) |
| 6,0 | 180 | consola urcă: intră groove-ul | stab + kick + boom + clap + crash | 1,25 | 2,25 (stabs) |
| 8,0 | 240 | camera zboară spre „Rulează agentul” | stab mare + kick + clap (+ crash în groove) | 1,25 | 2,25 (stabs) |
| 9,0 | 270 | butonul „Rulează agentul” e APĂSAT | stab foarte scurt + clap strâns | 1,25 | 2,25 (stabs) |
| 9,5 | 285 | „Perceive ✓” | o notă din motiv (coardă ciupită + clopoțel) | 1,25 | 1,25 (lead) |
| 10,0 | 300 | „Estimate ✓” | o notă din motiv (coardă ciupită + clopoțel) | 2,25 | 2,25 (lead) |
| 10,5 | 315 | „Decide ✓” | o notă din motiv (coardă ciupită + clopoțel) | 1,25 | 1,25 (lead) |
| 11,0 | 330 | „Act ✓” | o notă din motiv (coardă ciupită + clopoțel) | 2,25 | 1,25 (lead) |
| 11,5 | 345 | harta: traseele se desenează | 4 note în șaisprezecimi + rafală | 0,25 | 1,25 (lead) |
| 13,5 | 405 | lucrarea: scorul 0,87 și bilanțul postului | stab mare + kick + clap (+ crash în groove) | 1,25 | 1,25 (stabs) |
| 15,5 | 465 | cazul de tensiune: soluția cea mai ieftină | stab mare + kick + clap (+ crash în groove) | 2,25 | 2,25 (stabs) |
| 17,5 | 525 | cardul „Nu sunt sigur” (energia scade 1,5 s) | acord moale, filtrat; tobele se rup până la 19,0 | 4,25 | 3,25 (stabs) |
| 19,0 | 570 | „Aprobă” APĂSAT (energia revine) | stab + kick + clap + crash | 1,25 | 2,25 (stabs) |
| 22,0 | 660 | pastila neagră umple ecranul; cifra urcă 22,0-23,5 | stab + kick + boom + clap + crash | 1,25 | 1,25 (stabs) |
| 24,0 | 720 | al doilea rând de text | stab mare + kick + clap (+ crash în groove) | 1,25 | 1,25 (stabs) |
| 26,0 | 780 | logoul: soarele răsare peste traseu | A add9 mare + kick + boom + crash + clopoței; tobele se opresc | 2,25 | 1,25 (stabs) |

Toate 23 din 23 lovituri se regăsesc în mixaj. Mediana erorii absolute: **1,25 ms** în mixaj (maxim 4,25 ms) și 2,25 ms în stem-uri (maxim 3,25 ms), adică sub o zecime de cadru. Cele câteva milisecunde în plus vin din atacul de ~1 ms al sunetelor și din pasul detectorului.

### Verificări (măsurate, nu ascultate)

| Ce | Rezultat |
|---|---|
| Durata | 1.440.000 de eșantioane = 30,000000 s, 48 kHz, 24 de biți, stereo |
| Loudness integrat | -16,0 LUFS (ffmpeg ebur128); calcul propriu BS.1770 -16,02; loudnorm -16,17 |
| Vârf real (true peak) | -1,3 dBTP (ffmpeg), 0 eșantioane tăiate. Limitatorul lucrează doar pe drop (22,00-22,16 s), cel mult 1,5 dB |
| Plaja de loudness (LRA) | 3,4 LU |
| Pe secțiuni (LUFS, fără porți) | cârlig 0-6: -18,4; groove 6-17,5: -15,8; Nu sunt sigur 17,5-19: -19,6; Aprobă 19-20: -14,7; build 20-22: -15,6; drop 22-26: -15,1; final 26-29,9: -16,7 |
| Aerul de după „un plan.” | 2,5-3,0 s e cu 14 dB sub lovitura de pe 2,0 (RMS -28,8 față de -14,8 dBFS) |
| Ultimele 100 ms | zero digital |
| Suma stem-urilor | identică cu mixajul (0 LSB diferență) |
| Tempo | 120,0 BPM (autocorelația atacurilor din groove) |
| Pe grilă | 149 din 149 atacuri din mixaj cad la ±10 ms de grila de 32-imi; tobele 143/143 |
| Spectru, 2-6 kHz | fără vârfuri: cea mai mare bandă de 1/3 de octavă iese cu 1,5 dB peste vecine în groove și 2,4 dB în drop (la 2 kHz, unde spectrul începe să coboare); banda 2-6 kHz e cu 11,7 dB sub 300 Hz-2 kHz |
| Zona joasă | sub 120 Hz totul e mono (canalul lateral e cu 37 dB sub cel central); 125-250 Hz e cu 3,1 dB peste 500 Hz-1 kHz (cald, nu „bubuie”) |
| Mono | corelație L/R 0,95; în mono piesa e doar cu 0,2 dB mai încet |
| Determinism | două randări dau aceiași octeți, pe 9 fișiere (WAV, cele 6 stem-uri, cues, m4a) |

### Pentru montaj

- Puneți WAV-ul la cadrul 0. O bătaie = 15 cadre, o măsură = 60 de cadre: nu e nevoie de rotunjiri.
- Loviturile sunt fix pe cadru, fără umanizare. Lista completă, cu cadrul fiecăreia: `cues_120.json`, cheia `hits`.
- Stab-urile și motivul au un ecou discret de 3/16 (0,375 s, tot pe grilă). Dacă încurcă, coborâți stem-urile `stabs` și `lead`.
- Ce se schimbă ușor (în `compose_kinetic.py`, sus): `HITS` (loviturile și notele lor), `TIMELINE` (acordurile), `MIX_DB` (nivelurile). Loudness-ul final se reface singur la -16 LUFS.

### Ce trebuie ascultat de un om

Cifrele de mai sus nu spun cum sună. De ascultat o dată în căști și o dată pe difuzoarele laptopului sau ale videoproiectorului:

- dacă acordurile din cârlig (0-6 s) conduc față de kick-ul scurt de sub ele;
- dacă arpegiul care numără (22,0-23,5 s) se aude ca o numărătoare și nu e prea tare;
- dacă riserul și rafala din build (20-22 s) sunt de bun gust, nu prea „EDM”;
- acordul de pe 4,5 s (mi cu cvartă și terță, „Aceleași echipe.”) e îndrăzneț; dacă pare prea tensionat, scoateți G#5 din `HITS`;
- pe difuzoare mici basul (40-60 Hz) se aude mai slab; armonicele lui ar trebui să-l facă totuși simțit.

### Licență

Muzică originală compusă în cod de echipa CyberPunks pentru acest proiect, fără sample-uri. Publicată sub CC0 1.0 (domeniu public): oricine o poate folosi, fără nicio condiție.

*Original music composed in code by the CyberPunks team for this project, no samples. Released under CC0 1.0.*

## Varianta calmă: 96 BPM (prima)

Piesa de 30 de secunde pentru filmul de prezentare. Merge de la noapte (problema) la zori (planul).
Calmă, sigură pe ea, caldă, minimală. Fără voce, fără tobe grele.

- **30,000 s**, 96 BPM, 4/4, 12 măsuri a câte 2,5 s. O măsură = 75 de cadre la 30 fps.
- Tonalitatea: re major. Primele patru măsuri stau pe si minor („noaptea”). Acordul de re (tonica) apare abia pe 27,5 s: sosirea zorilor.
- Totul e sintetizat în Python (numpy și scipy): pian electric FM, pad filtrat, bas sub, kick dintr-un sinus al cărui ton coboară, hi-hat, clap și shaker din zgomot filtrat, coarde ciupite Karplus-Strong și reverb dintr-un răspuns la impuls sintetizat.
- Fără sample-uri, loop-uri sau soundfont-uri. Seed fix: la fiecare rulare iese exact același fișier, bit cu bit.

### Ce face muzica, măsură cu măsură

| Măsura | Timp (s) | Cadrul | Pe ecran | Muzica | Acord |
|---|---|---|---|---|---|
| 1 | 0,0-2,5 | 0 | negru, apoi mii de puncte: „2 milioane de contoare” | pad cald care urcă din liniște; ping-uri rare, sus (primul la 0,625 s) | Bsus |
| 2 | 2,5-5,0 | 75 | „192 de milioane de citiri pe zi” | ping-urile devin un șir liniștit de șaisprezecimi (fluxul de date) | Bsus |
| 3 | 5,0-7,5 | 150 | zoom pe un punct, „0,87” | șirul se oprește fix la 5,0 s; o notă sub (F#1) și o notă de pian (C#5) | F#7sus4 |
| 4 | 7,5-10,0 | 225 | „...nu îi spune unui tehnician unde să meargă mâine” | totul ține, filtrul se închide încet; de la 9,6875 s e aproape liniște (respirația) | F#7sus4 |
| 5 | 10,0-12,5 | 300 | numele produsului | pe 10,0 s se deschide armonia: primul acord plin, intră kick-ul moale și basul | Gmaj9 |
| 6 | 12,5-15,0 | 375 | semnalele A (12,5) și B (13,75) | groove: kick pe 1 și 3 (cade pe fiecare semnal), clap moale pe 2 și 4, hi-hat în optimi, linie de bas | Asus4 (add9) |
| 7 | 15,0-17,5 | 450 | semnalul C (15,0), apoi harta și Perceive (16,25) | același groove; prima notă a motivului (A4) cade pe Perceive | F#m11 |
| 8-9 | 17,5-22,5 | 525 | Estimate (17,5), Decide și bilanțul (18,75), Act și traseele (20,0) | groove complet; motivul B4, C#5, E5 cade pe fiecare pas, apoi rămâne suspendat pe F#5; partea cea mai caldă | Gmaj9, Asus → A6 |
| 10 | 22,5-25,0 | 675 | „Nu sunt sigur.” apoi „Un om decide.” | tobele și basul tac: pad plus un singur acord ținut, spațiu | Bm9 |
| 11 | 25,0-27,5 | 750 | metrica față de baseline | tobele revin, mai ușor; motivul revine și urcă | Gmaj9 → A6 |
| 12 | 27,5-30,0 | 825 | „CyberPunks · SmartHack XI 2026” | acord major de rezolvare fix pe 27,5 s, tobele tac, sună liber; liniște totală de la 29,9 s | D (add9) |

De ce așa:

- **Același pad, alt sens.** În măsurile 1-4 padul ține aceleași patru note (si, fa diez, do diez, mi). Nota sub din măsura 3 le schimbă rolul din „si minor” în „F#7sus4”, adică tensiune care cere o rezolvare.
- **Deschiderea de pe 10,0 s.** Basul urcă un semiton (fa diez → sol), iar armonia trece de la si minor la sol major (Gmaj9).
- **Groove-ul:** IV - V - iii - IV - V, adică Gmaj9, Asus, F#m11, Gmaj9, A. Vocile se mișcă foarte puțin: si și la rămân în pian aproape tot timpul.
- **„Nu sunt sigur.”** cade pe o cadență înșelătoare. Urechea așteaptă acordul de acasă după A și primește Bm9.
- **Finalul** e IV - V - I. Basul urcă do diez → re, iar motivul de 4 note se închide pe fa diez (F#5) fix pe 27,5 s.

### Fișierele

Toate stau în `out/`:

| Fișier | Ce e |
|---|---|
| `tura_96bpm_30s.wav` | mixajul: 48 kHz, 24 de biți, stereo, exact 1.440.000 de eșantioane (30,000 s) |
| `tura_96bpm_30s.m4a` | previzualizare AAC 256 kbps (ffmpeg); pentru montaj folosiți WAV-ul |
| `stems/` | `pad`, `keys`, `bass`, `drums`, `plucks`, `fx`; adunate dau exact mixajul (diferență 0) |
| `cues.json` | începutul fiecărei măsuri, fiecare timp, accentele cu nume (`silence_start`, `reveal`, `signals`, `steps`, `map`, `breakdown`, `metric`, `final_hit`, `silent_from`) și momentele exacte ale loviturilor (`events`) |
| `sfx_reveal.wav` | opțional: un val de aer mai prezent decât cel din mixaj, lung de o măsură (2,5 s). Pus la 7,5 s (cadrul 225), se termină fix pe 10,0 s (cadrul 300) |
| `sfx_tick.wav` | opțional: un tic moale de interfață, 90 ms, cu atacul pe primul eșantion |
| `spectrogram.png`, `waveform.png` | graficele de verificare, cu liniile de măsură |
| `report.json` | toate măsurătorile de mai jos |

În git intră doar m4a-ul, `cues.json`, graficele și raportul. WAV-urile se refac identic din cod (vezi `presentation/.gitignore`).

### Cum o refaci

Din rădăcina repo-ului:

```bash
uv run python presentation/music/compose.py
```

Durează cam 12 secunde. Scrie tot în `presentation/music/out/` și rulează verificările.

Opțiuni:

- `--out DOSAR`: scrie în alt dosar;
- `--no-m4a`: fără previzualizarea AAC;
- `--no-sfx`: fără cele două efecte separate;
- `--no-analyze`: fără verificări și grafice;
- `--hyperframes`: verifică ritmul și cu `npx hyperframes@0.9.19 beats` (cere internet).

Doar verificările, pe fișierele existente:

```bash
uv run python presentation/music/analyze.py --hyperframes
```

### Cum schimbi ceva

Toată compoziția stă în `compose.py`, în tabelul `CUE_MAP` de la începutul fișierului: o intrare pe măsură. Acolo sunt acordurile, nivelul și filtrul padului, loviturile de pian, basul, tobele, notele ciupite și efectele.

Accentele din `cues.json` se calculează din câmpul `section`. Dacă muți o secțiune într-o altă măsură, accentele se mută odată cu ea.

Nivelurile instrumentelor stau în `MIX_DB`. Loudness-ul final se reface singur la -16 LUFS.

### Pentru montaj

- Puneți WAV-ul la cadrul 0.
- Liniile de măsură cad pe cadre întregi: 0, 75, 150 ... 825.
- Timpii dintre ele cad pe sferturi de cadru (de exemplu 0,625 s = cadrul 18,75). Rotunjiți la cel mai apropiat cadru: eroarea e de cel mult 8 ms. La șaisprezecimi poate ajunge la o jumătate de cadru (17 ms).
- Kick-ul, notele motivului și acordurile de pe liniile de măsură sunt fix pe grilă. Hi-hat-ul, clap-ul și câteva note de pian au o umanizare de câteva milisecunde, fixă de la o rulare la alta.
- Respirația de dinaintea numelui (9,6875-10,0 s) e liniște digitală în toate stem-urile, în afară de `fx`. Acolo e un val foarte discret care intră în 10,0 s. Dacă nu vă place, dați mute la stem-ul `fx`.

### Verificări (măsurate, nu ascultate)

| Ce | Rezultat |
|---|---|
| Durata | 1.440.000 de eșantioane = 30,000000 s, 48 kHz, 24 de biți, stereo |
| Loudness integrat | -16,0 LUFS (ffmpeg ebur128); loudnorm -16,02; calcul propriu BS.1770 -16,03 |
| Vârf real (true peak) | -1,3 dBTP (ffmpeg), 0 eșantioane tăiate; limitatorul lucrează cel mult 1,4 dB, în total cam 0,6 s din 30, pe câțiva timpi tari (15,0; 20,0; 21,25; 26,5 s) |
| Plaja de loudness (LRA) | 7,6 LU |
| Ultimele 100 ms | zero digital; 29,5-29,9 s: -39 dBFS RMS (coada se stinge lin) |
| Respirația 9,69-10,0 s | -52,7 dBFS RMS, vârf -39,6 dBFS (doar valul din `fx`; fără el, zero digital) |
| Suma stem-urilor | identică cu mixajul (0 LSB diferență) |
| Spectru, 2-6 kHz | fără vârfuri: cea mai mare bandă de 1/3 de octavă iese cu 1,7 dB peste vecine; banda e cu 16 dB sub mediile 300 Hz-2 kHz |
| Zona joasă | 125-250 Hz doar cu 1,6 dB peste 500 Hz-1 kHz (nu „bubuie”); sub 120 Hz totul e mono |
| Mono | corelație L/R 0,89; în mono piesa e doar cu 0,34 dB mai încet |
| Pe grilă | 118 din 119 lovituri din partitură regăsite în mixaj, eroare mediană 2,8 ms; tobele 62/62 (0,8 ms), notele ciupite 41/41 (2,8 ms) |
| hyperframes beats | 96 BPM; în secțiunile ritmice beat-urile au o întârziere constantă de 15 ms (a detectorului), ±10 ms (pasul lui) |
| Determinism | două rulări dau fișiere identice bit cu bit |

Ce nu putem garanta din cifre: cum sună. Ascultați o dată în căști și o dată pe difuzoarele laptopului sau ale videoproiectorului.

### Licență

Muzică originală compusă în cod de echipa CyberPunks pentru acest proiect, fără sample-uri. Publicată sub CC0 1.0 (domeniu public): oricine o poate folosi, fără nicio condiție.

*Original music composed in code by the CyberPunks team for this project, no samples. Released under CC0 1.0.*
