# Status: Teo-prezentare
Actualizat: 2026-11-08 08:08
Milestone curent: PREDAREA (12:00). Filmul există ca draft complet; slideurile, scriptul final și înregistrarea de rezervă se fac acum (termene mai jos).
Gata de merge: NU se face merge din acest branch (istoria cu fișierele 3D); fișierele de predare se aduc în `Teo` individual (lista de mai jos).

## Starea finală (8 nov., 08:08): ce e gata și ce nu

| Ce | Stare | Unde | Mărime |
|---|---|---|---|
| Filmul cu „POWER” (pentru sală) | GATA ca draft complet (firul lateral, 7 nov. 19:42): 52,9 s, 1920×1080, 30 fps, -14,0 LUFS, vocea Kokoro (af_heart). Doar local: are piesa comercială | `presentation/frames-3d/threejs/film_v3/renders/local/daybreak_v3_draft.mp4` | 39,2 MB |
| Filmul versionat (fără „POWER”: voce + efecte) | ÎN LUCRU, gata la ~08:45 | `presentation/exports/daybreak-film.mp4` | țintă < 50 MB |
| Slideurile (PDF) | NU SUNT GATA (există doar planul `presentation/slides/OUTLINE.md`). În lucru acum, cu cifrele citite din `reports/`, gata la ~10:00 | `presentation/exports/daybreak-slides.pdf` | țintă < 5 MB |
| Scriptul demo-ului | Schiță veche (7 nov., 13:40: numele vechi, filmul de 30 s). Îl actualizez acum, gata la ~09:45 | `presentation/demo-script.md` | mic |
| Înregistrarea de rezervă a consolei | NU EXISTĂ. O fac acum din consola reală (API-ul pe 8710 merge; pornesc interfața pe 3710), gata la ~10:15. Doar local (peste 5 MB) | `presentation/exports/local/daybreak-demo-rezerva.mp4` | — |

Cifrele din vocea filmului, verificate în `reports/planner/agent_eval.json` (30 de zile, simulare): „30% less driving” = 10.565 km față de 15.439 km la „primul venit” (-31,6%); „fewer wasted trips” = 37% vizite inutile față de 63%; „eleven crews” = `config/crews.yaml` (11 echipe). De știut la demo: „556 problems” vine din consola de ieri; planul de azi pentru 8 iulie are 697 de lucrări la intrare (`outputs/demo/plans/demo-vara/plan.json`), deci la demo nu dăm alt număr de lucrări decât cel de pe ecran.

Fișierele mici de adus în `Teo` pentru predare (lista finală o confirm la ~10:15, după exporturi): `presentation/exports/daybreak-film.mp4`, `presentation/exports/daybreak-slides.pdf`, `presentation/demo-script.md`, `presentation/CREDITS.md`, `presentation/README.md`. Comanda, din `Teo`: `git checkout origin/Teo-prezentare -- <căile>`, apoi commit.

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
