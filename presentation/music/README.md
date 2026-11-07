# Muzica filmului „Tura de mâine”

Piesa de 30 de secunde pentru filmul de prezentare. Merge de la noapte (problema) la zori (planul).
Calmă, sigură pe ea, caldă, minimală. Fără voce, fără tobe grele.

- **30,000 s**, 96 BPM, 4/4, 12 măsuri a câte 2,5 s. O măsură = 75 de cadre la 30 fps.
- Tonalitatea: re major. Primele patru măsuri stau pe si minor („noaptea”). Acordul de re (tonica) apare abia pe 27,5 s: sosirea zorilor.
- Totul e sintetizat în Python (numpy și scipy): pian electric FM, pad filtrat, bas sub, kick dintr-un sinus al cărui ton coboară, hi-hat, clap și shaker din zgomot filtrat, coarde ciupite Karplus-Strong și reverb dintr-un răspuns la impuls sintetizat.
- Fără sample-uri, loop-uri sau soundfont-uri. Seed fix: la fiecare rulare iese exact același fișier, bit cu bit.

## Ce face muzica, măsură cu măsură

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

## Fișierele

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

## Cum o refaci

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

## Cum schimbi ceva

Toată compoziția stă în `compose.py`, în tabelul `CUE_MAP` de la începutul fișierului: o intrare pe măsură. Acolo sunt acordurile, nivelul și filtrul padului, loviturile de pian, basul, tobele, notele ciupite și efectele.

Accentele din `cues.json` se calculează din câmpul `section`. Dacă muți o secțiune într-o altă măsură, accentele se mută odată cu ea.

Nivelurile instrumentelor stau în `MIX_DB`. Loudness-ul final se reface singur la -16 LUFS.

## Pentru montaj

- Puneți WAV-ul la cadrul 0.
- Liniile de măsură cad pe cadre întregi: 0, 75, 150 ... 825.
- Timpii dintre ele cad pe sferturi de cadru (de exemplu 0,625 s = cadrul 18,75). Rotunjiți la cel mai apropiat cadru: eroarea e de cel mult 8 ms. La șaisprezecimi poate ajunge la o jumătate de cadru (17 ms).
- Kick-ul, notele motivului și acordurile de pe liniile de măsură sunt fix pe grilă. Hi-hat-ul, clap-ul și câteva note de pian au o umanizare de câteva milisecunde, fixă de la o rulare la alta.
- Respirația de dinaintea numelui (9,6875-10,0 s) e liniște digitală în toate stem-urile, în afară de `fx`. Acolo e un val foarte discret care intră în 10,0 s. Dacă nu vă place, dați mute la stem-ul `fx`.

## Verificări (măsurate, nu ascultate)

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

## Licență

Muzică originală compusă în cod de echipa CyberPunks pentru acest proiect, fără sample-uri. Publicată sub CC0 1.0 (domeniu public): oricine o poate folosi, fără nicio condiție.

*Original music composed in code by the CyberPunks team for this project, no samples. Released under CC0 1.0.*
