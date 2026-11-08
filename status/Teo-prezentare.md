# Status: Teo-prezentare
Actualizat: 2026-11-08 09:25
Milestone curent: PREDAREA (12:00). Toate livrabilele prezentării sunt gata: filmul, slideurile, scriptul demo-ului și înregistrarea de rezervă.
Gata de merge: NU se face merge din acest branch (istoria cu fișierele 3D); fișierele de predare se aduc în `Teo` individual (comanda de mai jos).

## Starea finală (8 nov., 08:05)

| Ce | Stare | Unde | Mărime |
|---|---|---|---|
| Filmul final, exportul versionat (cel predat) | GATA: 52,9 s, 1920×1080, 30 fps, H.264, AAC 48 kHz, -14,0 LUFS, vârf -1,8 dBTP, faststart. Imaginea filmului v3 („lume în miniatură”), cu vocea (Kokoro, af_heart) și efectele, FĂRĂ „POWER” | `presentation/exports/daybreak-film.mp4` | 38,7 MB |
| Filmul pentru sală | GATA: aceeași imagine, cu „POWER” (-14,0 LUFS). Doar local, ignorat de git | `presentation/exports/local/daybreak-film-power.mp4` | 39,2 MB |
| Slideurile | GATA: 16 pagini (11 principale, 5 anexă), în română, cifrele citite din `reports/` de `presentation/scripts/build_slides.py` (scriptul tipărește tabelul cifrelor cu fișierul și cheia) | `presentation/exports/daybreak-slides.pdf` | 1,5 MB |
| Scriptul demo-ului | GATA: cronometrul pe 5 minute, cifrele de pe slideuri, planul B, întrebările probabile | `presentation/demo-script.md` | mic |
| Înregistrarea de rezervă a consolei | GATA (08:15): 2:08, fără sunet, consola reală (planul, rularea agentului, detaliul unei lucrări cu contor, coada „Nu sunt sigur” cu Aprobă, alertele). Doar local, ignorată de git | `presentation/exports/local/daybreak-demo-rezerva.mp4` | 7,5 MB |
| README și credite | GATA, cu livrabilele finale, vocea Kokoro (Apache-2.0), imaginile AI, muzica doar local | `presentation/README.md`, `presentation/CREDITS.md` | mici |

Verificat: `tests/test_repo_size.py` trece. La 08:00 am scos din urmărire fișierele grele urcate peste noapte în acest branch (58 de planșe QA mărite, 522 MB; o scenă Blender de 11 MB; două foi de 5,6 MB; încercările planșelor; audio-ul m4a/flac). Rămân pe disc. Sunt însă în istoria de pe GitHub (commiturile din 7 nov., 18:51 și 19:33): de adăugat la curățarea pe care o decide Teo.

Cifrele din film și de pe slideuri, din `reports/`: +49% valoare netă, 10.515 față de 15.439 km (-31,9%, în film „30% less driving”), 37% față de 63% vizite degeaba (simulare de 30 de zile, față de „primul venit, primul servit”); A 0,62/0,02 (subtile) și 0,80/0,11 (SGCC); B PR-AUC 0,28/0,15; C 0,0054/0,0227 pu; bilanț F1 0,75/0,48. De știut: filmul spune „556 problems” (consola de ieri); planul de azi are alt număr de lucrări, deci live spunem doar ce e pe ecran.

### Refăcut pe rapoartele finale din `Teo` (09:25)

`reports/` e luat din `origin/Teo`; slideurile sunt reconstruite cu `presentation/scripts/build_slides.py`, iar tabelul cifrelor e verificat. Ce s-a schimbat pe slideuri: bilanțul are F1 0,75 față de 0,48 (slideurile 6 și 7), agentul 10.515 km și 31,9% mai puțin (slideul 9). Fuziunea bilanțului nu mai apare nicăieri (pe slideul 6 e diagnosticul cauzei, pe slideul 7 cele 84% din energia pierdută găsită). Precizia@K de 1,00 a lui A nu apare. Scriptul demo-ului și creditele au valorile noi.

Cifrele din film, față de rapoartele finale (filmul nu e re-randat):
- A și bilanț: filmul nu spune nicio cifră a lor.
- „Thirty percent less driving”, „30%” pe ecran (replica 12, 39,35-42,58 s, scena `s12`): corect, raportul dă -31,9%.
- „Fewer wasted trips” (aceeași replică): corect, 37% față de 63%.
- „Eleven crews”, „11 crews” pe ecran (replica 4, de la 15,2 s, scena `s04`): corect, `config/crews.yaml` are 11 echipe.
- „Five hundred and fifty-six problems”, „556 problems” pe ecran (replica 4, 16,5-18,4 s, scena `s04`): NU mai corespunde. Consola servește acum 653 de lucrări (`/api/plan`, plan regenerat azi, se schimbă între rulări), iar `demo_day.work_items` din `agent_eval.json` e 532. E singura cifră din film care nu se potrivește.

### Fișierele de adus în `Teo` pentru predare

Din `Teo` (toate sub 5 MB, în afară de film, care e singurul export, sub 50 MB):

```bash
git fetch origin
git checkout origin/Teo-prezentare -- presentation/exports/daybreak-film.mp4 presentation/exports/daybreak-slides.pdf presentation/demo-script.md presentation/CREDITS.md presentation/README.md
git commit -m "Predare: filmul Daybreak, slideurile și scriptul demo-ului (din Teo-prezentare)"
```

Opțional, pentru reproducere: `presentation/scripts/build_slides.py` și `presentation/scripts/export_film_public.sh`. Atenție: au nevoie de activele care sunt doar în `Teo-prezentare` (fonturile din `presentation/video/assets/fonts/`, planșele din `presentation/frames-3d/plates_v3/raw_jpg/`, vocea și efectele locale), deci în `Teo` nu rulează singure. Copia pentru sală și înregistrarea de rezervă rămân doar pe laptopul lui Teo.

## Făcut
- 12:50 Citite instrucțiunile, memoria, planul și contractele. `uv sync` și `make check` trec.
- 12:58 HyperFrames 0.9.19 instalat local (`presentation/video/`). Testul de 2 secunde randat: H.264 High, 1920×1080, 30 fps, yuv420p, 60 de cadre, diacriticele ș ț corecte (randat în 3,4 s).
- 13:00 Articolul lui leo citit integral; regulile și aplicarea lor în `presentation/STYLE.md` (3 culori: noapte #07090D, hârtie #F2EFE8, chihlimbar #FFA53D; font Hanken Grotesk, OFL).
- 13:00 Codex (image 2.6) a generat 5 imagini (contor, stâlp cu transformator, panouri solare, furtună, zori), prompturile în `presentation/assets/gen/PROMPTS.md`.
- 13:05 Harta reală a României noaptea (NASA Black Marble 2016, GIBS) cu cele 3 regiuni Rețele Electrice conturate (geoBoundaries, CC BY 4.0).
- 13:15 Cele 8 scene ale filmului scrise și animate (schiță), `hyperframes check` trece cu 0 erori. Storyboard-ul (11 cadre statice) în `presentation/video/STORYBOARD.md` și `presentation/video/boards/storyboard.html`.
- 13:20 Storyboard-ul arătat lui Teo (11 cadre) și prima variantă animată, fără muzică.
- 13:35 Filmul trece pe sistemul produsului, după răspunsul orchestratorului: font Archivo (ca în consolă), fundal cerneala logoului #0B1622, text hârtie #F5F4F0, logoul "răsărit pe traseu" animat la nume și la final, markerii surselor A/B/C în culorile consolei. Chihlimbarul rămâne doar pentru soarele din logo, zori și sursa C; traseele și opririle agentului sunt în hârtie. Ziua reală 8 iulie 2025 apare în scena semnalelor (vijelie în Banat, tensiune la prânz în București). `hyperframes check` trece.
- 13:31 Merge din `Teo` (bilanț pe post, scara de soluții); `make check` trece (38 de teste). Bilanțul intră în scena agentului, la pasul Decide ("Bilanțul confirmă": energia ieșită din post față de cea facturată).
- 13:37 Merge din `Teo` (documentul cu problemele reale PPC 2026); cifrele noi (prosumatori ANRE aug. 2026, compensații, CPT, integrarea contoarelor) și slideul de context 2026 sunt în `presentation/slides/OUTLINE.md`, cu data și sursa.
- 13:40 Muzica originală gata (subagent): 96 BPM, 30,000 s, -16,0 LUFS, -1,3 dBTP, compusă în cod, CC0, `presentation/music/`. Motivul ei cade pe Perceive, Estimate, Decide, Act; kick-ul pe fiecare semnal.
- 13:43 Primul export cu sunet (v0): H.264 High, BT.709, 1920×1080, 30 fps, AAC 48 kHz, -16,1 LUFS, vârf -1,1 dBTP, 15,4 MB. Pornite cele două review-uri independente: vizual (Claude) și tehnic (Codex).
- Planul slideurilor (`presentation/slides/OUTLINE.md`) și prima schiță a scriptului de demo (`presentation/demo-script.md`).

- 13:45 Teo a respins varianta 1 ("prea banal, greu de văzut, culori nașpa") și a dat o referință (film Trust). Studiul referinței: `presentation/research/REFERINTA-trust.md` (2 tăieturi în 21 s, alb pur, text de 150-190 px, un accent, obiecte 3D, interfața la scară uriașă, final pe negru, ~134 BPM).
- 14:20 Filmul nou în 9 scene (`presentation/video/compositions/k1-k9`): alb, text uriaș, obiecte 3D (Codex), consola REALĂ capturată din http://localhost:3710/ la rezoluție dublă (agent-browser, server local), cifrele citite din `reports/` și din `outputs/demo/` de `presentation/scripts/cifre_film.py`. `hyperframes check` trece.
- 14:26 12 cadre-cheie cu textul final și timpii, arătate lui Teo (`presentation/video/boards/kf/`). Animarea completă vine după "da".
- În lucru: obiecte 3D adevărate în Blender (Codex Sol și Astra în paralel, calitate maximă), muzica nouă de 120 BPM (subagent).

- 14:37 Teo: cadrele variantei 2 sunt "confuze". Varianta 3: 6 momente, cuvinte de zi cu zi, fără jargon (fără Perceive/Estimate/Decide/Act, bilanț, 1,10 pe ecran; acestea rămân în slideuri și demo). Textul trimis lui Teo spre aprobare; animez după "da".
- Abilități folosite la varianta 3 (până acum): `hyperframes`, `motion-doctrine`, `reference-to-motion` (structura cârligului din referință). La animare: `apple-design`, `apple-launch-film`, `cut-the-curve`, `seam-craft`, `oversized-cursor`, `motion-effects`, `milestone-reveal`, `gsap-timeline`/`gsap-core`/`gsap-performance`.
- 14:37 Greșeală reparată: commitul 2625d9e a inclus din greșeală folderele de lucru 3D (154 MB, 365 de fișiere, o arhivă de 47 MB). Scoase din urmărire și ignorate (commit 9d973f2). Rămân în istorie: vezi cererea către orchestrator.

- 15:05 Varianta 3 terminată ca cadre cheie (36 s, scenele c1-c7, `presentation/scripts/build_film_v3.py`): textele în zona sigură a cadrului, fiecare rând stă cât să fie citit, `hyperframes check` fără erori. Commit b0537d5.
- 15:10 Teo a ales muzica: "POWER" (Kanye West, instrumental), doar pentru prezentarea din sală. Copia pentru HyperFrames e în `presentation/video/assets/audio/local/`, iar exporturile cu ea merg în `presentation/exports/local/`; amândouă sunt ignorate de git (au propriul `.gitignore`). Bătăile, măsurate din fișier: 77 BPM, o măsură de 3,12 s, tobele intră la 9,475 s.
- 15:20 Teo a oprit filmul: fără MP4 și fără aliniere pe "POWER" până aprobă cadrele statice. N-am randat nimic.
- 15:40 Trei schițe HTML de cadre (hook, produs, hartă), în engleză, cu harta desenată din nou: `presentation/video/boards/v4/` (`presentation/scripts/build_boards_v4.py`). Puse pe pauză după decizia de la 15:35; nu le-am trimis lui Teo.
- 15:55 Structura filmului Daybreak pe cele 10 cadre din `presentation/frames-codex/v1/FRAMES.md`: `presentation/video/STORYBOARD.md` (textul de pe ecran, ce află privitorul, sursa fiecărei afirmații, ritmul propus pe "POWER" pentru când repornim). Acolo sunt și 5 observații pentru textele din FRAMES.md.
- Abilități folosite la cadrele variantei 3: `hyperframes`, `hyperframes-cli` (check, snapshot), `motion-doctrine`, `apple-design`, `apple-launch-film`, `launch-video`, `oversized-cursor`, `reference-to-motion`. La schițele variantei 4: `apple-design`, `apple-launch-film`, `frontend-design`, `hyperframes-cli`.

- 16:14 Merge din `Teo` (numele Daybreak în README și plan, cifrele finale pentru M2). Cifra din film rămâne +49%: agentul 1.051.842 lei față de 706.556 lei la „primul venit, primul servit” (30 de zile, sămânța 7), din `reports/planner/agent_eval.json`, finală pentru M2.

- 17:20 Regula lui Teo pentru fișierele grele (17:15): merge din `Teo` (regulile din `.gitignore` și `tests/test_repo_size.py`). Niciun fișier urmărit nu mai cade sub reguli: folderele 3D erau scoase din 9d973f2, iar wav-urile n-au fost niciodată urmărite. Am scos din urmărire și audio-ul mic rămas (3 fișiere m4a și un flac, 1-1,7 MB), cu reguli noi în `presentation/.gitignore`; fișierele rămân pe disc și se refac cu `make music`. `tests/test_repo_size.py` trece. Istoria n-am atins-o: în ea rămân `presentation/assets/3d-sol/3d-sol.zip` (44,9 MB) și randările 3D din 2625d9e, pentru curățarea pe care o decide Teo după înghețare.

## Urmează
- Aștept alegerea lui Teo din firul lateral (logoul nou, paleta, cadrele Codex). După "da": scenele HyperFrames după cadrele aprobate, apoi filmul, în două exporturi: local cu "POWER" și versionat cu muzică fără drepturi de autor.
- Slideurile, cu numele Daybreak.
- Slideurile: șablonul HTML și `build_slides.py`, care citește cifrele din `reports/` (fără cifre scrise de mână), export PDF.
- După 01:00: capturi reale din consolă (cadrele 5 și 6); după 21:30: cifra față de baseline din `reports/` (cadrul 7).

## Blocaje
- Niciunul.

## Cereri către orchestrator
- URGENT, înainte de înghețarea de la 10:30 (găsit la înregistrarea de rezervă, vizibil pentru juriu):
  1. Interfață: după „Aprobă” în „Nu sunt sigur” apare un mesaj roșu: „Decizia nu s-a salvat. API-ul nu a răspuns la timp.” Decizia se salvează totuși (jurnalul arată aprobarea și planul refăcut). Cauza probabilă: `postReview` din `web/lib/data/api.ts` folosește timpul de așteptare implicit de 1.500 ms (`web/lib/data/config.ts`), iar API-ul reface planul în circa 5 s. De mărit timpul de așteptare pe `POST /review`. Mesajul apare și în înregistrarea de rezervă (1:22-1:30); dacă se repară până la 10:30, refac înregistrarea.
  2. Interfață: contorul „Nu sunt sigur” rămâne la 25 după aprobare (lista se reface abia după recalculare).
  3. API: înregistrarea a rulat agentul de 3 ori și a aprobat de 2 ori un element B pe API-ul de pe 8710, deci planul `demo-vara` nu mai e cel inițial. Înainte de demo (13:00), API-ul trebuie repornit sau resetat la starea curată.
  4. De știut: planul nu iese identic între rulări (de exemplu 291,8 față de 366,1 km), deci la demo citim cifrele de pe ecran. Etichetele „Perceive/Estimate/Decide/Act” sunt în engleză, restul interfeței în română.
- JURNAL (17:20): în `memory/journal.md` din worktree-ul meu sunt două rânduri scrise de firul lateral și necomise (16:15, cadrele Codex respinse și varianta 2; 17:05, Teo alege stilul „lume în miniatură” în 3D adevărat). Eu nu scriu în `memory/`; vă rog să le treceți în jurnalul din `Teo`.
- (rezolvat 16:10) NUME NOU (15:30): Teo a schimbat numele produsului în **Daybreak** (în locul lui "Tura de mâine"). De schimbat: interfața (titlul paginii, antetul, `web/public/brand/`), README-ul și slideurile (pe ale mele le schimb eu); decizia intră în `memory/journal.md`. Atenție: logoul cu soarele peste traseu e respins, cu toate variantele lui. Logoul nou îl alege Teo dintre conceptele din `presentation/brand-lab/r2/logos/` (firul lateral), așa că în `web/public/brand/` deocamdată se schimbă doar numele.
- (rezolvat 16:10) Pentru jurnal (n-am voie în `memory/`): la 14:46 agentul de muzică a compus varianta de 120 BPM (`presentation/music/compose_kinetic.py`, CC0, 30,000 s, -16,0 LUFS); de la 15:10 filmul folosește "POWER" local, iar varianta de 120 BPM rămâne de rezervă.
- ISTORIE (16:20: Teo păstrează deocamdată fișierele 3D, pentru că se pot folosi la video; la final orchestratorul se asigură că nu intră în git, iar până atunci nu face merge din `Teo-prezentare` în `Teo`. Eu nu mai adaug fișiere mari în commituri): commitul 2625d9e de pe `Teo-prezentare` conține din greșeală `presentation/assets/3d-astra/` și `presentation/assets/3d-sol/` (154 MB, inclusiv `3d-sol.zip` de 47 MB). Le-am scos din urmărire în 9d973f2, dar sunt în istorie. Înainte de repo-ul public (decizia lui Teo de la 11:00): `git filter-repo --path presentation/assets/3d-astra --path presentation/assets/3d-sol --invert-paths` pe ramurile care conțin commitul, apoi force-push (eu n-am voie). Dacă faceți merge din `Teo-prezentare` în `Teo` înainte de curățare, istoria crește cu 154 MB.
- (rezolvat 16:20: A a plafonat procentele, API-ul servește datele noi, 0 din 689 de lucrări mai au astfel de procente; capturile noi din consolă sunt curate) Bug vizibil pentru juriu, în consola reală (coada "Nu sunt sigur", `/coada`): factori de tipul "Consumul de noapte a crescut cu 18273047% față de istoric" (și 25359262%, 19488814%). Probabil împărțire la un istoric aproape zero în textul factorului (firul A sau șablonul de text). Ar trebui plafonat sau formulat altfel ("de la aproape zero").
- (la interfață, 16:10; datele bilanțului sunt în `Teo`) Pagina postului (`/posturi/PT-0267`) spune "Bilanțul pe acest post nu e calculat încă": filmul folosește deocamdată curbe ilustrative pentru bilanț; când intră bilanțul în consolă, capturez pagina reală.
- (rezolvat 13:20) Harta întunecată și cardul "Nu sunt sigur" în `/demo`: cerute interfeței de orchestrator. Mulțumesc.
- (rezolvat 13:20) Cifra principală: valoarea capturată din `reports/planner/agent_eval.json` față de cea mai bună strategie simplă; în slideuri și metrica principală a fiecărui model din `reports/<X>/metrics.json`.
- (rezolvat 16:10: finale pentru M2, aduse prin merge) Nou: când există `reports/planner/agent_eval.json` și `reports/<A|B|C>/metrics.json` în `Teo`, vă rog spuneți-mi (sau le iau eu la verificarea de la 21:30).

## Cum se rulează (comenzile exacte)
- `make presentation-assets` (harta NASA, granițele, schița scenei 5)
- `make video-check` (verificările HyperFrames)
- `make video-preview` (previzualizare pe portul 3720), `make video-preview-stop`
- `make video-render` (exportul final în `presentation/exports/`)
- `make music` (refacerea muzicii, identică bit cu bit, și copia FLAC din proiectul video)
- Exportul unei variante de lucru: `bash presentation/scripts/export_video.sh <nume> presentation/video/renders/tmp`

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
- 14:30 Abilități noi pentru HyperFrames, instalate la nivel de utilizator (`~/.claude/skills`), nu în repo. HeyGen hyperframes @336abaa (Apache-2.0): hyperframes, hyperframes-cli, hyperframes-registry, media-use, reverse-any-video, style-sampling, slideshow, plus doctrina lor de mișcare (motion-doctrine, seam-craft, cut-the-curve, oversized-cursor). charlie947/motion-graphics-skills @229022e (MIT): apple-launch-film, launch-video, reference-to-motion, milestone-reveal, animated-chart, motion-effects, motion-brief-writer, motion-prompt-writer, brand-intake, title-sequence-3d. greensock/gsap-skills @aed9cfd (MIT): gsap-core, gsap-timeline, gsap-utils, gsap-performance, gsap-plugins. Respins imMamdouhaboammar/motion-graphics-skills: licență proprietară.

- 15:10 Muzica: "POWER" (instrumental) doar în exportul local pentru sală; nu intră în git și nici în exporturile versionate (acolo merge muzică fără drepturi de autor).
- 15:20 Filmul e oprit până aprobă Teo cadrele statice.
- 15:30 Numele produsului: Daybreak. Toate textele din film în engleză, cel mult 5 cuvinte pe cadru.
- 15:30 Respinse: logoul cu soarele peste traseu (cu variantele lui) și planșa `presentation/brand-lab/daybreak-directions.*`. Identitatea se reface în firul lateral; până alege Teo, nu fixăm culori, logo sau 3D în scene. Pe cadre apare doar cuvântul "Daybreak".
- 15:35 Cadrele se generează cu Codex image (stil Apple, colorate), în firul lateral: `presentation/frames-codex/v1/` (nu scriu acolo).
- 15:45 "Homes go dark" (fostul "Zeci de mii de case fără curent"): sursa e prefectul Timișului, circa 40.000 de consumatori afectați, cumulat 7-9 iulie 2025 (`docs/research/B.md`). Pe ecran rămâne fără cifră.
- 16:10 Regulă nouă (orchestratorul): niciun fișier peste 5 MB în git, în afară de exportul final (sub 50 MB). Verificat: de la mine nu e niciunul (cel mai mare e de 1,3 MB).
- 17:15 Regulă (Teo, prin orchestrator): randările 3D, arhivele, audio-ul și video-urile brute stau doar pe disc. În git intră doar fișiere sub 5 MB și, la final, un singur export al filmului, sub 50 MB. Istoria nu o rescriu eu.
