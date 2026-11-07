# Planet Daybreak — testul Blender

Scenă 3D procedurală pentru filmul de 30 s. Randările curente sunt cele șase momente din camera furnizată de echipa Three.js, plus trei dovezi ale transformării sferă–plan. Filmul de 900 de cadre nu a fost pornit. Randările albe și `daybreak.blend` sunt păstrate.

## Fișiere

- `daybreak_planet.blend`: geometrie reală, Geometry Nodes, particule de păr, materiale PBR împachetate și lumini.
- `stills/planet_storm.png` (1,5 s), `planet_problems.png` (7,5 s), `planet_map.png` (9,8 s), `planet_routes.png` (14 s), `planet_dawn.png` (23 s), `planet_outro.png` (28,5 s).
- `stills/morph_1.png`, `morph_05.png`, `morph_0.png`: factor 1, 0,5 și 0, cameră fixă, fără DOF pentru comparație.
- `stills/contact_sheet.jpg`, `planet_contact_sheet.jpg`, `morph_contact_sheet.jpg`.
- `tracks.json`: câte opt ancore proiectate pentru fiecare dintre cele nouă PNG, inclusiv ascunderea geometrică și vizibilitatea în cadru.
- `assets/camera_path.json`: copia traseului primit la 18:37, toate cele 900 de cadre. Hash-ul exportului este inclus în verificarea livrării.
- `qa/planet_delivery_check.json`: timpi, hash-ul scenei și verificări. `planet_timings.jsonl` păstrează și încercările mai vechi; sinteza selectează exclusiv hash-ul scenei livrate.

Toate PNG-urile livrate au 1920×1080, RGB și nu conțin text sau logo. Nu există un MP4 nou: zborul de 8 s a fost înlocuit de acest test, conform schimbării de brief.

## Comenzi exacte

Din `/Users/teo/.t3/worktrees/CyberPunks/Teo-prezentare`:

```bash
python3 presentation/frames-3d/blender/scripts/fetch_assets.py

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -t 12 --python-exit-code 1 -P presentation/frames-3d/blender/scripts/build_planet.py

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak_planet.blend -t 12 --python-exit-code 1 -P presentation/frames-3d/blender/scripts/verify_morph.py

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -t 12 --python-exit-code 1 -P presentation/frames-3d/blender/scripts/verify_camera_import.py

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak_planet.blend -t 12 --python-exit-code 1 -P presentation/frames-3d/blender/scripts/render_planet.py -- --mode final --engine CYCLES --width 1920 --samples 512

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak_planet.blend -t 12 --python-exit-code 1 -P presentation/frames-3d/blender/scripts/render_planet.py -- --mode morph --engine CYCLES --width 1920 --samples 256

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak_planet.blend -t 12 --python-exit-code 1 -P presentation/frames-3d/blender/scripts/render_planet.py -- --mode benchmark --engine CYCLES --width 1920 --samples 64

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak_planet.blend -t 12 --python-exit-code 1 -P presentation/frames-3d/blender/scripts/render_planet.py -- --mode benchmark --engine EEVEE --width 1920 --samples 128

/opt/homebrew/bin/python3.14 -I -B presentation/frames-3d/blender/scripts/package_planet.py
```

Pentru iterații: `--mode preview --width 960 --samples 64 --moments storm routes`; acestea scriu în `qa/`. `--camera-path` acceptă un export nou în aceeași schemă. `--hero` oferă o cameră separată pentru inspecție, dar cele șase livrabile folosesc camera filmului.

Constructorul refolosește sursa `build_scene.py`, fără să suprascrie fișierul alb. Sămânța este `270611`. Se salvează un singur `.blend` pentru planeta actuală; cele 29 de fișiere PBR/HDRI sunt împachetate în el. Descărcătorul verifică MD5. Nu este necesar internet la randarea scenei salvate.

## Construcție și aspect

Macheta are raza de 0,36 m. Cele 40 de case au lățimi, adâncimi, înălțimi, nuanțe de var și pante ale acoperișului diferite; 27 sunt pe calota satului principal. Există nouă anexe mici, grădini, garduri din stinghii, jgheaburi, cărămizi expuse, rame, coșuri și țigle individuale neregulate. Texturile scanate controlează culoarea, rugozitatea și normalele, cu uzură suplimentară a varului și murdărie la bază.

Terenul are relief fizic neuniform, crustă de pământ și mușchi, pietricele, petice de sol și 360.000 de fire de iarbă părinte cu șase copii interpolate. Iarba are lungime variabilă, aproximativ 3,8 mm maxim, și culoare diferită pe fir. Drumurile sunt din pământ/pietriș cu șleauri, margini neregulate și 3.000 de pietricele separate. Asfaltul este folosit doar în depou. Modelul nu are plintă netedă.

Nucii au trunchiuri, ramuri și frunze individuale parțial translucide. Câmpul are 264 de floarea-soarelui cu tulpini, frunze, petale și semințe. Stâlpii sunt din beton, cu izolatoare și fire calculate ca lănțișoare suspendate. Camioanele sunt albe cu dungă portocalie `FA4616`, brațe articulate pliate și cupe goale; lucrătorii au veste portocalii și benzi reflectorizante. Panglicile satin folosesc `FA4616`, `00A3E0`, `163FE8`.

Norul randat are formă neregulată și 7.000 de fibre curbate geometrice. Fibrele sunt curbe reale convertite în plasă; iarba folosește sistemul real de particule de păr. Nu se suprapune un al doilea emitter de păr pe nor. Firul de suspendare și firele de ploaie sunt geometrie vizibilă. Iluminarea folosește HDRI de studio, cheie caldă/rece după moment, umplere și lumini mici reale în depou. Fundalul este navy `000F1E`; AgX schimbă valorile pixelilor ca la o expunere fotografică. Materialul, nu pixelul final, are culoarea PPC exactă.

## Camera filmului și transformarea

Importul respectă poziția, ținta, FOV-ul și deplasarea lentilei din fiecare cadru. Convenția Three.js Y-up devine Blender Z-up prin `(x,y,z) → (x,−z,y) × 0,36 m`. Lentila este 85 mm, cu lățime de senzor ajustată pentru FOV-ul exportat. `shift_x = sx/2`, `shift_y = sy/2 × 9/16`. Diafragma se convertește din raza aperturii exportate; focalizarea este reală, pe sat. Pentru gros-planul răsăritului, focalizarea urmărește casa din prim-plan și diafragma este f/9, ca planul de claritate să nu rămână în spatele caselor. Poziția, FOV-ul și deplasarea camerei rămân cele exportate. O probă independentă a verificat 20,700 de proiecții în toate cele 900 de cadre: eroarea maximă este **0.113 pixeli**.

`Planet_Control["flat_to_planet"]` controlează toate cele 16 grupuri geometrice și cele opt ancore printr-un singur grup Geometry Nodes nativ. `1` este sfera, `0` planul tangent la polul nord. Pentru un punct la distanța r de centru, unghiul este `factor × r / R`, iar raza curburii este `R / factor`; limita zero este planul. Casele și vehiculele se rotesc rigid în cadrul tangent, terenul și drumurile se curbează per vârf. Verificarea numerică a celor trei stări este în `qa/morph_check.json`. Părul se ascunde în transferul spre plan, pentru a evita întinderea fibrelor.

La 9,8 s exportul actualizat are factorul **0.00000** și arată harta complet plată. Livrarea respectă acel cadru; `morph_0.png` oferă și o probă separată din camera fixă. Harta PPC curată, textele și discul Soarelui se suprapun în HyperFrames, conform separării din traseul primit. Răsăritul Blender conține lumina direcțională reală și linia zi/noapte. Primul cadru are planeta mai mică deoarece camera aprobată încă se apropie; cadrul de lucru o aduce mai aproape.

## Ancore

Coordonatele sunt pixeli cu origine sus-stânga, x spre dreapta și y în jos. Ancore: `fallen_pole`, `meter`, `hot_roof`, `depot`, `unsure_house`, `truck_1`, `truck_2`, `truck_3`. Pozițiile sunt extrase din vârfurile evaluate de Geometry Nodes, apoi proiectate prin camera importată. `occluded` folosește o rază prin geometria vizibilă la randare; `visible` combină testul de ascundere cu încadrarea. Unele ancore sunt deliberat în spate sau în afara cadrului. Camioanele au poziții distincte de noapte, parcare, traseu și convoi.

## Timpi măsurați, 1080p

Blender 5.2.1 LTS, Apple M5 Max, Metal GPU 32 de nuclee, CPU exclus din Cycles. Cycles: OIDN, eșantionare adaptivă cu prag 0,015, opt ricoșee, persistent data, AgX Medium High Contrast. Cadre finale: maximum 512 samples; dovada morph: 256. Proba de cost cerută: 64. EEVEE: 128 samples, ray tracing activ, persistent data.

Timpii includ pregătirea stării/camerei, evaluarea scenei, randarea, denoise și scrierea PNG. Nu includ lansarea Blender sau construcția scenei. Fiecare benchmark primește un cadru de încălzire, exclus din medie. Prima randare finală poate include compilare Metal; este păstrată ca măsurare rece. Numărul de samples este plafonul, nu numărul efectiv folosit în fiecare pixel. Eșantionarea adaptivă implicită a fost verificată ca activă. Sistemul are 36 GB RAM; în timpul probei Cycles 64 erau folosiți circa 16,9 GB de swap. Sesiunea nu a fost un benchmark izolat. Presiunea de memorie poate explica de ce proba de 64 a ieșit uneori mai lentă decât randările anterioare la 512. Estimarea folosește valorile efectiv măsurate, ca buget conservator, și trebuie reverificată într-un lot continuu înainte de filmul complet.

| Moment | Cycles 512, s | Cycles 64, s | EEVEE 128, s |
|---|---:|---:|---:|
| storm | 18.970 | 16.119 | 7.401 |
| problems | 22.914 | 20.615 | 7.560 |
| map | 13.930 | 12.887 | 3.727 |
| routes | 23.524 | 33.525 | 7.036 |
| dawn | 22.013 | 37.614 | 6.626 |
| outro | 14.110 | 11.633 | 8.936 |

Ponderând cele șase stări după durata actelor, Cycles 64 are **25.66 s/cadru**, deci **384.9 min/900 cadre**. EEVEE 128 are **7.26 s/cadru**, deci **108.9 min/900 cadre**. Acestea sunt extrapolări, nu măsurători ale unui film complet. Vederile apropiate, animația actorilor, motion blur, costul compoziției și încărcarea calculatorului pot schimba totalul. Pentru Cycles 512, extrapolarea brută este 310.0 min, dar include costul rece al primului cadru și nu este o medie stabilă de secvență.

## Proveniența resurselor

Toate cele opt resurse sunt CC0, conform [licenței oficiale Poly Haven](https://polyhaven.com/license). Manifestul păstrează numele, URL-ul resursei, URL-urile exacte de descărcare, rezoluțiile și MD5 pentru toate cele 29 de fișiere.

| Resursă și URL | Licență | Fișiere |
|---|---|---|
| [clay_roof_tiles_02](https://polyhaven.com/a/clay_roof_tiles_02) | CC0-1.0 | Diffuse 2k, Rough 2k, nor_gl 2k, Displacement 1k |
| [white_plaster_rough_01](https://polyhaven.com/a/white_plaster_rough_01) | CC0-1.0 | Diffuse 2k, Rough 2k, nor_gl 2k, Displacement 1k |
| [gravel_road](https://polyhaven.com/a/gravel_road) | CC0-1.0 | Diffuse 2k, Rough 2k, nor_gl 2k, Displacement 1k |
| [asphalt_02](https://polyhaven.com/a/asphalt_02) | CC0-1.0 | Diffuse 2k, Rough 2k, nor_gl 2k, Displacement 1k |
| [bark_brown_02](https://polyhaven.com/a/bark_brown_02) | CC0-1.0 | Diffuse 2k, Rough 2k, nor_gl 2k, Displacement 1k |
| [european_walnut_veneer_04](https://polyhaven.com/a/european_walnut_veneer_04) | CC0-1.0 | Diffuse 2k, Rough 2k, nor_gl 2k, Displacement 1k |
| [grass_ground](https://polyhaven.com/a/grass_ground) | CC0-1.0 | Diffuse 2k, Rough 2k, nor_gl 2k, Displacement 1k |
| [studio_small_03](https://polyhaven.com/a/studio_small_03) | CC0-1.0 | hdri 4k |

URL-uri exacte:

- clay_roof_tiles_02 / Diffuse: [clay_roof_tiles_02_diff_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/clay_roof_tiles_02/clay_roof_tiles_02_diff_2k.jpg)
- clay_roof_tiles_02 / Rough: [clay_roof_tiles_02_rough_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/clay_roof_tiles_02/clay_roof_tiles_02_rough_2k.jpg)
- clay_roof_tiles_02 / nor_gl: [clay_roof_tiles_02_nor_gl_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/clay_roof_tiles_02/clay_roof_tiles_02_nor_gl_2k.jpg)
- clay_roof_tiles_02 / Displacement: [clay_roof_tiles_02_disp_1k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/clay_roof_tiles_02/clay_roof_tiles_02_disp_1k.jpg)
- white_plaster_rough_01 / Diffuse: [white_plaster_rough_01_diff_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/white_plaster_rough_01/white_plaster_rough_01_diff_2k.jpg)
- white_plaster_rough_01 / Rough: [white_plaster_rough_01_rough_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/white_plaster_rough_01/white_plaster_rough_01_rough_2k.jpg)
- white_plaster_rough_01 / nor_gl: [white_plaster_rough_01_nor_gl_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/white_plaster_rough_01/white_plaster_rough_01_nor_gl_2k.jpg)
- white_plaster_rough_01 / Displacement: [white_plaster_rough_01_disp_1k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/white_plaster_rough_01/white_plaster_rough_01_disp_1k.jpg)
- gravel_road / Diffuse: [gravel_road_diff_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/gravel_road/gravel_road_diff_2k.jpg)
- gravel_road / Rough: [gravel_road_rough_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/gravel_road/gravel_road_rough_2k.jpg)
- gravel_road / nor_gl: [gravel_road_nor_gl_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/gravel_road/gravel_road_nor_gl_2k.jpg)
- gravel_road / Displacement: [gravel_road_disp_1k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/gravel_road/gravel_road_disp_1k.jpg)
- asphalt_02 / Diffuse: [asphalt_02_diff_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/asphalt_02/asphalt_02_diff_2k.jpg)
- asphalt_02 / Rough: [asphalt_02_rough_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/asphalt_02/asphalt_02_rough_2k.jpg)
- asphalt_02 / nor_gl: [asphalt_02_nor_gl_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/asphalt_02/asphalt_02_nor_gl_2k.jpg)
- asphalt_02 / Displacement: [asphalt_02_disp_1k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/asphalt_02/asphalt_02_disp_1k.jpg)
- bark_brown_02 / Diffuse: [bark_brown_02_diff_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/bark_brown_02/bark_brown_02_diff_2k.jpg)
- bark_brown_02 / Rough: [bark_brown_02_rough_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/bark_brown_02/bark_brown_02_rough_2k.jpg)
- bark_brown_02 / nor_gl: [bark_brown_02_nor_gl_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/bark_brown_02/bark_brown_02_nor_gl_2k.jpg)
- bark_brown_02 / Displacement: [bark_brown_02_disp_1k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/bark_brown_02/bark_brown_02_disp_1k.jpg)
- european_walnut_veneer_04 / Diffuse: [european_walnut_veneer_04_diff_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/european_walnut_veneer_04/european_walnut_veneer_04_diff_2k.jpg)
- european_walnut_veneer_04 / Rough: [european_walnut_veneer_04_rough_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/european_walnut_veneer_04/european_walnut_veneer_04_rough_2k.jpg)
- european_walnut_veneer_04 / nor_gl: [european_walnut_veneer_04_nor_gl_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/european_walnut_veneer_04/european_walnut_veneer_04_nor_gl_2k.jpg)
- european_walnut_veneer_04 / Displacement: [european_walnut_veneer_04_disp_1k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/european_walnut_veneer_04/european_walnut_veneer_04_disp_1k.jpg)
- grass_ground / Diffuse: [grass_ground_diff_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/grass_ground/grass_ground_diff_2k.jpg)
- grass_ground / Rough: [grass_ground_rough_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/grass_ground/grass_ground_rough_2k.jpg)
- grass_ground / nor_gl: [grass_ground_nor_gl_2k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/grass_ground/grass_ground_nor_gl_2k.jpg)
- grass_ground / Displacement: [grass_ground_disp_1k.jpg](https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/grass_ground/grass_ground_disp_1k.jpg)
- studio_small_03 / hdri: [studio_small_03_4k.hdr](https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/studio_small_03_4k.hdr)

## Ce este verificat și ce rămâne

Verificarea automată cere nouă PNG curente la dimensiunea corectă, opt ancore finite pentru fiecare, trei imagini morph diferite, același hash al scenei și toate cele șase măsurători în fiecare motor. Sunt livrate și verificările independente ale transformării și camerei.

Acesta rămâne un test de aspect și integrare. Fațadele au încă o familie stilistică comună; conceptul are uzură și varietate arhitecturală mai bogate. În exportul de cameră primit, unele cadre apropiate taie marginea planetei; poziția camerei nu a fost schimbată pentru a compensa acest lucru. Norul păstrează o formă mai sculptată decât bumbacul din referință, iar panglica portocalie se deschide spre pastel sub AgX și lumina de studio. Iarba poate pierde fibre fine în vederile depărtate după denoise. Proba intermediară arată geometria întinsă a emisferei opuse, care va fi acoperită de harta 2D în film. Camioanele și panglicile au poziții pentru cele șase momente, dar mișcarea lor continuă nu este încă validată. Nu este declarată acceptarea fotografică de către un editor și nu s-a pornit filmul complet.
