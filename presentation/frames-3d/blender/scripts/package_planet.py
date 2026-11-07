"""Check the exact rendered blend, nine stills, camera/morph proofs and engine benchmarks."""
from pathlib import Path
from PIL import Image
import json, math, hashlib
ROOT=Path(__file__).resolve().parents[1]
BEATS=['storm','problems','map','routes','dawn','outro']; MORPH=['morph_1','morph_05','morph_0']
NAMES=['planet_'+b for b in BEATS]+MORPH
scene_hash=hashlib.sha256((ROOT/'daybreak_planet.blend').read_bytes()).hexdigest()
tracks=json.loads((ROOT/'tracks.json').read_text()); required={'fallen_pole','meter','hot_roof','depot','unsure_house','truck_1','truck_2','truck_3'}
for name in NAMES:
    with Image.open(ROOT/'stills'/(name+'.png')) as im: assert im.size==(1920,1080) and im.mode=='RGB',(name,im.size,im.mode)
    entry=tracks['entries'][name]; assert entry['scene_sha256']==scene_hash,('Stale still',name)
    assert set(entry['anchors'])==required,name
    for a in entry['anchors'].values(): assert math.isfinite(a['x']) and math.isfinite(a['y'])
assert [tracks['entries'][n]['factor'] for n in MORPH]==[1,.5,0]
assert len({hashlib.sha256((ROOT/'stills'/(n+'.png')).read_bytes()).hexdigest() for n in MORPH})==3
sheet=Image.new('RGB',(1920,720),'#000F1E')
for i,b in enumerate(BEATS):
    with Image.open(ROOT/'stills'/('planet_'+b+'.png')) as im: sheet.paste(im.resize((640,360),Image.Resampling.LANCZOS),((i%3)*640,(i//3)*360))
for filename in ['contact_sheet.jpg','planet_contact_sheet.jpg']: sheet.save(ROOT/'stills'/filename,quality=96,subsampling=0)
proof=Image.new('RGB',(1920,360),'#000F1E')
for i,name in enumerate(MORPH):
    with Image.open(ROOT/'stills'/(name+'.png')) as im: proof.paste(im.resize((640,360),Image.Resampling.LANCZOS),(i*640,0))
proof.save(ROOT/'stills'/'morph_contact_sheet.jpg',quality=96,subsampling=0)
records=[json.loads(line) for line in (ROOT/'planet_timings.jsonl').read_text().splitlines()]
groups={key:{} for key in ['CYCLES_512','CYCLES_64','EEVEE_128']}
for r in records:
    if r.get('scene_sha256')!=scene_hash or r['width']!=1920 or r.get('camera_source')!='camera_path.json' or not r['name'].startswith('planet_'): continue
    key=r['engine']+'_'+str(r['samples'])
    if key in groups and ((key=='CYCLES_512' and r['kind']=='final') or (key!='CYCLES_512' and r['kind']=='benchmark')): groups[key][r['name'][7:]]=r
for key,group in groups.items(): assert set(group)==set(BEATS),(key,list(group))
durations={'storm':6.4,'problems':3.074,'map':.835,'routes':10.191,'dawn':5.4,'outro':4.1}
weighted={key:sum(group[b]['seconds']*durations[b] for b in BEATS)/30 for key,group in groups.items()}
camera_check=json.loads((ROOT/'qa'/'camera_import_check.json').read_text()); assert camera_check['passes_one_pixel']
morph_check=json.loads((ROOT/'qa'/'morph_check.json').read_text())
summary={'scene_sha256':scene_hash,'camera_path_sha256':hashlib.sha256((ROOT/'assets'/'camera_path.json').read_bytes()).hexdigest(),'resolution':[1920,1080],'duration_weights_seconds':durations,'weighted_seconds_per_frame':weighted,'estimated_900_seconds':{k:v*900 for k,v in weighted.items()},'measured':{k:{b:group[b] for b in BEATS} for k,group in groups.items()},'camera_check':camera_check,'morph_check':morph_check,'tracks_entries':9,'anchors_each':8,'validation':'Nine current-scene RGB PNGs at 1920x1080; eight finite anchors each; three distinct morph states; six measured moments per renderer.'}
(ROOT/'qa'/'planet_delivery_check.json').write_text(json.dumps(summary,indent=2)+'\n')
assets=json.loads((ROOT/'assets'/'manifest.json').read_text())
asset_rows='\n'.join('| ['+a['name']+']('+a['asset_url']+') | '+a['license']+' | '+', '.join(k+' '+f['resolution'] for k,f in a['files'].items())+' |' for a in assets)
file_urls='\n'.join('- '+a['name']+' / '+k+': ['+f['local']+']('+f['url']+')' for a in assets for k,f in a['files'].items())
timing_rows='\n'.join('| '+b+' | '+' | '.join(f'{groups[k][b]["seconds"]:.3f}' for k in groups)+' |' for b in BEATS)
commands=[]
BL='/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b'
script='presentation/frames-3d/blender/scripts/'
blend='presentation/frames-3d/blender/daybreak_planet.blend'
commands=['python3 '+script+'fetch_assets.py', BL+' -t 12 --python-exit-code 1 -P '+script+'build_planet.py', BL+' '+blend+' -t 12 --python-exit-code 1 -P '+script+'verify_morph.py',BL+' -t 12 --python-exit-code 1 -P '+script+'verify_camera_import.py']
for mode,engine,samples in [('final','CYCLES',512),('morph','CYCLES',256),('benchmark','CYCLES',64),('benchmark','EEVEE',128)]: commands.append(BL+' '+blend+' -t 12 --python-exit-code 1 -P '+script+'render_planet.py -- --mode '+mode+' --engine '+engine+' --width 1920 --samples '+str(samples))
commands.append('/opt/homebrew/bin/python3.14 -I -B '+script+'package_planet.py')
command_text='\n\n'.join(commands)
readme=f'''# Planet Daybreak — testul Blender

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
{command_text}
```

Pentru iterații: `--mode preview --width 960 --samples 64 --moments storm routes`; acestea scriu în `qa/`. `--camera-path` acceptă un export nou în aceeași schemă. `--hero` oferă o cameră separată pentru inspecție, dar cele șase livrabile folosesc camera filmului.

Constructorul refolosește sursa `build_scene.py`, fără să suprascrie fișierul alb. Sămânța este `270611`. Se salvează un singur `.blend` pentru planeta actuală; cele 29 de fișiere PBR/HDRI sunt împachetate în el. Descărcătorul verifică MD5. Nu este necesar internet la randarea scenei salvate.

## Construcție și aspect

Macheta are raza de 0,36 m. Cele 40 de case au lățimi, adâncimi, înălțimi, nuanțe de var și pante ale acoperișului diferite; 27 sunt pe calota satului principal. Există nouă anexe mici, grădini, garduri din stinghii, jgheaburi, cărămizi expuse, rame, coșuri și țigle individuale neregulate. Texturile scanate controlează culoarea, rugozitatea și normalele, cu uzură suplimentară a varului și murdărie la bază.

Terenul are relief fizic neuniform, crustă de pământ și mușchi, pietricele, petice de sol și 360.000 de fire de iarbă părinte cu șase copii interpolate. Iarba are lungime variabilă, aproximativ 3,8 mm maxim, și culoare diferită pe fir. Drumurile sunt din pământ/pietriș cu șleauri, margini neregulate și 3.000 de pietricele separate. Asfaltul este folosit doar în depou. Modelul nu are plintă netedă.

Nucii au trunchiuri, ramuri și frunze individuale parțial translucide. Câmpul are 264 de floarea-soarelui cu tulpini, frunze, petale și semințe. Stâlpii sunt din beton, cu izolatoare și fire calculate ca lănțișoare suspendate. Camioanele sunt albe cu dungă portocalie `FA4616`, brațe articulate pliate și cupe goale; lucrătorii au veste portocalii și benzi reflectorizante. Panglicile satin folosesc `FA4616`, `00A3E0`, `163FE8`.

Norul randat are formă neregulată și 7.000 de fibre curbate geometrice. Fibrele sunt curbe reale convertite în plasă; iarba folosește sistemul real de particule de păr. Nu se suprapune un al doilea emitter de păr pe nor. Firul de suspendare și firele de ploaie sunt geometrie vizibilă. Iluminarea folosește HDRI de studio, cheie caldă/rece după moment, umplere și lumini mici reale în depou. Fundalul este navy `000F1E`; AgX schimbă valorile pixelilor ca la o expunere fotografică. Materialul, nu pixelul final, are culoarea PPC exactă.

## Camera filmului și transformarea

Importul respectă poziția, ținta, FOV-ul și deplasarea lentilei din fiecare cadru. Convenția Three.js Y-up devine Blender Z-up prin `(x,y,z) → (x,−z,y) × 0,36 m`. Lentila este 85 mm, cu lățime de senzor ajustată pentru FOV-ul exportat. `shift_x = sx/2`, `shift_y = sy/2 × 9/16`. Diafragma se convertește din raza aperturii exportate; focalizarea este reală, pe sat. Pentru gros-planul răsăritului, focalizarea urmărește casa din prim-plan și diafragma este f/9, ca planul de claritate să nu rămână în spatele caselor. Poziția, FOV-ul și deplasarea camerei rămân cele exportate. O probă independentă a verificat {camera_check['projections']:,} de proiecții în toate cele 900 de cadre: eroarea maximă este **{camera_check['max_error_pixels']:.3f} pixeli**.

`Planet_Control["flat_to_planet"]` controlează toate cele 16 grupuri geometrice și cele opt ancore printr-un singur grup Geometry Nodes nativ. `1` este sfera, `0` planul tangent la polul nord. Pentru un punct la distanța r de centru, unghiul este `factor × r / R`, iar raza curburii este `R / factor`; limita zero este planul. Casele și vehiculele se rotesc rigid în cadrul tangent, terenul și drumurile se curbează per vârf. Verificarea numerică a celor trei stări este în `qa/morph_check.json`. Părul se ascunde în transferul spre plan, pentru a evita întinderea fibrelor.

La 9,8 s exportul actualizat are factorul **{tracks['entries']['planet_map']['factor']:.5f}** și arată harta complet plată. Livrarea respectă acel cadru; `morph_0.png` oferă și o probă separată din camera fixă. Harta PPC curată, textele și discul Soarelui se suprapun în HyperFrames, conform separării din traseul primit. Răsăritul Blender conține lumina direcțională reală și linia zi/noapte. Primul cadru are planeta mai mică deoarece camera aprobată încă se apropie; cadrul de lucru o aduce mai aproape.

## Ancore

Coordonatele sunt pixeli cu origine sus-stânga, x spre dreapta și y în jos. Ancore: `fallen_pole`, `meter`, `hot_roof`, `depot`, `unsure_house`, `truck_1`, `truck_2`, `truck_3`. Pozițiile sunt extrase din vârfurile evaluate de Geometry Nodes, apoi proiectate prin camera importată. `occluded` folosește o rază prin geometria vizibilă la randare; `visible` combină testul de ascundere cu încadrarea. Unele ancore sunt deliberat în spate sau în afara cadrului. Camioanele au poziții distincte de noapte, parcare, traseu și convoi.

## Timpi măsurați, 1080p

Blender 5.2.1 LTS, Apple M5 Max, Metal GPU 32 de nuclee, CPU exclus din Cycles. Cycles: OIDN, eșantionare adaptivă cu prag 0,015, opt ricoșee, persistent data, AgX Medium High Contrast. Cadre finale: maximum 512 samples; dovada morph: 256. Proba de cost cerută: 64. EEVEE: 128 samples, ray tracing activ, persistent data.

Timpii includ pregătirea stării/camerei, evaluarea scenei, randarea, denoise și scrierea PNG. Nu includ lansarea Blender sau construcția scenei. Fiecare benchmark primește un cadru de încălzire, exclus din medie. Prima randare finală poate include compilare Metal; este păstrată ca măsurare rece. Numărul de samples este plafonul, nu numărul efectiv folosit în fiecare pixel. Eșantionarea adaptivă implicită a fost verificată ca activă. Sistemul are 36 GB RAM; în timpul probei Cycles 64 erau folosiți circa 16,9 GB de swap. Sesiunea nu a fost un benchmark izolat. Presiunea de memorie poate explica de ce proba de 64 a ieșit uneori mai lentă decât randările anterioare la 512. Estimarea folosește valorile efectiv măsurate, ca buget conservator, și trebuie reverificată într-un lot continuu înainte de filmul complet.

| Moment | Cycles 512, s | Cycles 64, s | EEVEE 128, s |
|---|---:|---:|---:|
{timing_rows}

Ponderând cele șase stări după durata actelor, Cycles 64 are **{weighted['CYCLES_64']:.2f} s/cadru**, deci **{weighted['CYCLES_64']*15:.1f} min/900 cadre**. EEVEE 128 are **{weighted['EEVEE_128']:.2f} s/cadru**, deci **{weighted['EEVEE_128']*15:.1f} min/900 cadre**. Acestea sunt extrapolări, nu măsurători ale unui film complet. Vederile apropiate, animația actorilor, motion blur, costul compoziției și încărcarea calculatorului pot schimba totalul. Pentru Cycles 512, extrapolarea brută este {weighted['CYCLES_512']*15:.1f} min, dar include costul rece al primului cadru și nu este o medie stabilă de secvență.

## Proveniența resurselor

Toate cele opt resurse sunt CC0, conform [licenței oficiale Poly Haven](https://polyhaven.com/license). Manifestul păstrează numele, URL-ul resursei, URL-urile exacte de descărcare, rezoluțiile și MD5 pentru toate cele 29 de fișiere.

| Resursă și URL | Licență | Fișiere |
|---|---|---|
{asset_rows}

URL-uri exacte:

{file_urls}

## Ce este verificat și ce rămâne

Verificarea automată cere nouă PNG curente la dimensiunea corectă, opt ancore finite pentru fiecare, trei imagini morph diferite, același hash al scenei și toate cele șase măsurători în fiecare motor. Sunt livrate și verificările independente ale transformării și camerei.

Acesta rămâne un test de aspect și integrare. Fațadele au încă o familie stilistică comună; conceptul are uzură și varietate arhitecturală mai bogate. În exportul de cameră primit, unele cadre apropiate taie marginea planetei; poziția camerei nu a fost schimbată pentru a compensa acest lucru. Norul păstrează o formă mai sculptată decât bumbacul din referință, iar panglica portocalie se deschide spre pastel sub AgX și lumina de studio. Iarba poate pierde fibre fine în vederile depărtate după denoise. Proba intermediară arată geometria întinsă a emisferei opuse, care va fi acoperită de harta 2D în film. Camioanele și panglicile au poziții pentru cele șase momente, dar mișcarea lor continuă nu este încă validată. Nu este declarată acceptarea fotografică de către un editor și nu s-a pornit filmul complet.
'''
(ROOT/'README.md').write_text(readme)
print(json.dumps({'scene_sha256':scene_hash,'weighted_seconds_per_frame':weighted,'estimated_900_minutes':{k:v*15 for k,v in weighted.items()},'checks':'passed'},indent=2))
