"""Validate the Planet Daybreak delivery, build contact sheets and write the reproducible README."""
from pathlib import Path
from PIL import Image
import json,statistics,math
ROOT=Path(__file__).resolve().parents[1]
BEATS=['storm','problems','map','routes','dawn','outro']; MORPH=['morph_1','morph_05','morph_0']
NAMES=['planet_'+b for b in BEATS]+MORPH
tracks=json.loads((ROOT/'tracks.json').read_text()); required={'fallen_pole','meter','hot_roof','depot','unsure_house','truck_1','truck_2','truck_3'}
for name in NAMES:
    with Image.open(ROOT/'stills'/(name+'.png')) as im: assert im.size==(1920,1080),(name,im.size)
    entry=tracks['entries'][name]; assert set(entry['anchors'])==required,name
    for a in entry['anchors'].values(): assert math.isfinite(a['x']) and math.isfinite(a['y'])
assert [tracks['entries'][n]['factor'] for n in MORPH]==[1,.5,0]
sheet=Image.new('RGB',(1920,1080),'#000F1E')
for i,b in enumerate(BEATS):
    with Image.open(ROOT/'stills'/('planet_'+b+'.png')) as im: sheet.paste(im.resize((640,360),Image.Resampling.LANCZOS),((i%3)*640,(i//3)*360))
sheet.save(ROOT/'stills'/'contact_sheet.jpg',quality=96,subsampling=0)
sheet.save(ROOT/'stills'/'planet_contact_sheet.jpg',quality=96,subsampling=0)
proof=Image.new('RGB',(1920,360),'#000F1E')
for i,name in enumerate(MORPH):
    with Image.open(ROOT/'stills'/(name+'.png')) as im: proof.paste(im.resize((640,360),Image.Resampling.LANCZOS),(i*640,0))
proof.save(ROOT/'stills'/'morph_contact_sheet.jpg',quality=96,subsampling=0)
records=[json.loads(line) for line in (ROOT/'planet_timings.jsonl').read_text().splitlines()]
cycles={}; eevee={}
for r in records:
    if r['width']!=1920: continue
    if r['engine']=='CYCLES' and r['kind']=='final': cycles[r['name']]=r
    if r['engine']=='EEVEE' and r['kind']=='benchmark' and r['name'].startswith('planet_'): eevee[r['name']]=r
assert set(cycles)>={f'planet_{b}' for b in BEATS}; assert set(eevee)>={f'planet_{b}' for b in BEATS}
# Approximate state durations from the approved 30-second timeline, not 900 measured frames.
durations={'storm':6.4,'problems':3.074,'map':.835,'routes':10.191,'dawn':5.4,'outro':4.1}
cavg=sum(cycles['planet_'+b]['seconds']*durations[b] for b in BEATS)/30
eavg=sum(eevee['planet_'+b]['seconds']*durations[b] for b in BEATS)/30
summary={'resolution':[1920,1080],'cycles_samples':512,'eevee_samples':128,'duration_weights_seconds':durations,'weighted_cycles_seconds_per_frame':cavg,'weighted_eevee_seconds_per_frame':eavg,'estimated_900_cycles_seconds':cavg*900,'estimated_900_eevee_seconds':eavg*900,'measured':{'CYCLES':{b:cycles['planet_'+b]['seconds'] for b in BEATS},'EEVEE':{b:eevee['planet_'+b]['seconds'] for b in BEATS}},'tracks_entries':len(NAMES),'anchors_each':8,'validation':'All nine PNG dimensions, factors, finite anchor coordinates, six engine timings checked.'}
(ROOT/'qa'/'planet_delivery_check.json').write_text(json.dumps(summary,indent=2)+'\n')
assets=json.loads((ROOT/'assets'/'manifest.json').read_text())
asset_rows='\n'.join('| ['+a['name']+']('+a['asset_url']+') | '+a['license']+' | '+', '.join(k+' '+f['resolution'] for k,f in a['files'].items())+' |' for a in assets)
file_urls='\n'.join('- '+a['name']+' / '+k+': ['+f['local']+']('+f['url']+')' for a in assets for k,f in a['files'].items())
timing_rows='\n'.join(f'| {b} | {cycles["planet_"+b]["seconds"]:.3f} | {eevee["planet_"+b]["seconds"]:.3f} |' for b in BEATS)
readme=f'''# Planet Daybreak, testul Blender pentru M1

Scenă procedurală, reală, pentru stratul 3D al filmului. Sursele, materialele, luminile și geometria sunt în `daybreak_planet.blend`. Cele cinci randări ale machetei albe au rămas în `stills/`, cu numele lor inițiale. Livrarea curentă este planeta pictată, nu zborul de 8 secunde sau filmul complet de 900 de cadre.

## Livrare

- `stills/planet_storm.png`, 1,5 s: noapte, ferestre și depou luminate, nor din fibre și ploaie fizică.
- `stills/planet_problems.png`, 7,5 s: trei lumini locale pentru stâlp, contor și acoperiș.
- `stills/planet_map.png`, 9,8 s: vedere verticală, hartă PPC plată cu amprente albe și drumuri cyan.
- `stills/planet_routes.png`, 14 s: trei panglici satin, trei camioane pe trasee și două în depou.
- `stills/planet_dawn.png`, 23 s: lumină solară oblică, sfera portocalie la orizont și o parte a satului încă în umbră.
- `stills/planet_outro.png`, 28,5 s: planetă mică în fundalul navy.
- `stills/morph_1.png`, `morph_05.png`, `morph_0.png`: același control la 1, 0,5 și 0.
- `stills/contact_sheet.jpg`, `planet_contact_sheet.jpg` și `morph_contact_sheet.jpg`.
- `tracks.json`: nouă capturi, fiecare cu cele opt ancore cerute, în pixeli 1920×1080.

Toate cele nouă PNG sunt 1920×1080, RGB, fără text, fonturi sau logo. Nu conțin muzică.

## Reconstrucție și randare

Din directorul proiectului:

```bash
cd /Users/teo/.t3/worktrees/CyberPunks/Teo-prezentare

python3 presentation/frames-3d/blender/scripts/fetch_assets.py

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -t 12 --python-exit-code 1 -P presentation/frames-3d/blender/scripts/build_planet.py

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak_planet.blend -t 12 --python-exit-code 1 -P presentation/frames-3d/blender/scripts/render_planet.py -- --mode final --engine CYCLES --width 1920 --samples 512

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak_planet.blend -t 12 --python-exit-code 1 -P presentation/frames-3d/blender/scripts/render_planet.py -- --mode morph --engine CYCLES --width 1920 --samples 512

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak_planet.blend -t 12 --python-exit-code 1 -P presentation/frames-3d/blender/scripts/render_planet.py -- --mode benchmark --engine EEVEE --width 1920 --samples 128

/opt/homebrew/bin/python3.14 -I -B presentation/frames-3d/blender/scripts/package_planet.py
```

`build_planet.py` citește constructorul original `build_scene.py`, îi refolosește casele, mașinile, stâlpii și detaliile, apoi face scena planetei fără să suprascrie `daybreak.blend`. Sămânța rămâne `270611`. Imaginile PBR și HDRI sunt împachetate în noul fișier `.blend`; o randare din el nu depinde de conexiunea la internet. Pentru reconstrucție, descărcătorul verifică MD5 pentru fiecare fișier din manifest.

Pentru o probă mai rapidă, folosiți `--mode preview --width 960 --samples 96 --moments storm routes dawn`. Rezultatele de probă intră în `qa/`. Nu înlocuiesc cadrele finale.

## Geometrie, lumină și material

Satul are 40 de case cu dimensiuni, poziții, planuri și orientări diferite. Nouă case formează satul vizibil, cu drumuri curbe, depou, nuci, câmp cu 264 de plante de floarea-soarelui, lucrători, câine, pisică, rufe și un termos. Restul continuă pe partea opusă. Casele au goluri și suprafețe retrase la ferestre, muchii mici și țigle individuale cu abateri fine. PBR-urile sunt folosite efectiv pentru culoare, rugozitate și normale, nu doar descărcate.

Terenul are 240.000 de fire părinte de iarbă, cu cinci fire copil interpolate pentru fiecare, generate cu sistemul real de particule pentru păr al Blender. Norul are 6.000 de fire părinte din bumbac și cinci copii. Emitterele au repausul pe sferă, pentru a evita fire rămase pe planul plat. Firele se ascund în faza de desfacere și în harta curată. Frunzele sunt geometrii individuale cu material parțial translucid.

Iluminarea combină HDRI de studio, cheie caldă, umplere rece, lumini reale în depou și un Soare direcțional pentru răsărit. Fiecare grup de ferestre are un control separat `window_house_XX` pe scenă. Paleta atribuită materialelor este navy `000F1E`, portocaliu `FA4616`, cyan `00A3E0`, albastru `163FE8`. AgX modifică firesc valorile finale ale pixelilor ca la orice material fotografiat.

Camerele sunt perspective, cu focalizare reală pe un obiect-țintă, diafragmă de 1,4–2,8 pentru cadrele de planetă și nouă lame de diafragmă. Harta și dovada tehnică folosesc camere ortografice, cu profunzime mare. Nu există bloom, flare sau efect de neon.

## Un singur control pentru sferă și hartă

În Blender, obiectul `Planet_Control` are proprietatea `flat_to_planet`:

- `1`: sat radial pe sfera de 0,32 m rază.
- `0,5`: stare intermediară.
- `0`: sat plat, cu aceleași componente.

Pământul și drumurile folosesc interpolarea pozițiilor fiecărui vârf. Casele, figurinele și vehiculele folosesc cadre tangente radiale, cu o corecție de rotație la mijloc bazată pe cuaternioni. Aceasta păstrează volumul caselor la jumătatea transformării. Toate cheile depind de aceeași proprietate.

Harta PPC este o compoziție deasupra stării plate, pentru transferul către interfață. Camera ei arată satul principal, fără casele de pe emisfera opusă. Importul viitorului `camera_path.json` nu este încă făcut; testul folosește șase camere din momentele cerute, nu o animație finală de 30 de secunde.

## Ancore pentru compoziția 2D

`tracks.json` folosește origine în colțul stânga-sus, `x` spre dreapta, `y` în jos. Fiecare intrare include timpul, factorul, camera, pozițiile în metri și proiecțiile în pixeli pentru `fallen_pole`, `meter`, `hot_roof`, `depot`, `unsure_house`, `truck_1`, `truck_2`, `truck_3`.

`in_frame` testează cadrul camerei. `occluded` folosește o rază reală prin geometrie, iar `visible` combină cele două. Nu toate ancorele sunt vizibile din fiecare unghi. Punctele camioanelor sunt deasupra brațului pliat, potrivite pentru etichete. Ele schimbă poziția între depou, trasee și convoi. Acesta este spațiu Blender, drept, Z în sus, în metri; viitoarea cameră Three.js trebuie convertită din convenția ei înainte de import.

## Timpi măsurați și costul celor 900 de cadre

Blender 5.2.1 LTS, Apple M5 Max, Cycles pe Metal GPU cu 32 de nuclee. CPU este exclus din dispozitivele Cycles. Cadrele finale au 512 eșantioane maxime, prag adaptiv 0,01, denoise, AgX Medium High Contrast și opt ricoșee maxime. EEVEE are 128 de eșantioane temporale și ray tracing activ. EEVEE primește o randare de încălzire înaintea celor șase probe de măsurare.

Duratele includ randarea, denoise unde se aplică și scrierea PNG. Nu includ lansarea Blender sau reconstrucția scenei. Primul cadru Cycles include pregătirea inițială a scenei pe GPU.

| Moment | Cycles 512, secunde | EEVEE 128, secunde |
|---|---:|---:|
{timing_rows}

Cu ponderi după durata fiecărui act din filmul aprobat, media estimată este **{cavg:.2f} s/cadru pentru Cycles** și **{eavg:.2f} s/cadru pentru EEVEE**. Pentru 900 de cadre rezultă **{cavg*900/60:.1f} minute în Cycles**, respectiv **{eavg*900/60:.1f} minute în EEVEE**. Acestea sunt extrapolări din șase vederi, nu un film de 900 de cadre deja randat. Mișcarea reală a camerei, gros-planul de la 18,5 s, motion blur și costul compoziției pot schimba totalul. Calitatea finală planificată rămâne Cycles.

Măsurătorile brute sunt în `planet_timings.jsonl`; sinteza și verificarea dimensiunilor sunt în `qa/planet_delivery_check.json`.

## Surse Poly Haven și licențe

Toate cele opt resurse sunt CC0-1.0, conform [licenței oficiale Poly Haven](https://polyhaven.com/license). Numele, URL-urile, rezoluțiile, mărimile și MD5 sunt păstrate în `assets/manifest.json`.

| Resursă și URL | Licență | Hărți descărcate |
|---|---|---|
{asset_rows}

URL-urile exacte ale tuturor fișierelor descărcate:

{file_urls}

## Revizuire și limite

Cele șase momente și cele trei stări de transformare sunt randări efective din aceeași scenă. Au fost verificate dimensiunile, absența textului, încadrarea, focalizarea, acoperirea terenului, firele, paleta și proiecțiile ancorelor.

Fațadele păstrează o stilizare mai simplă decât casele foarte îmbătrânite din imaginile de concept. Transformarea intermediară este o demonstrație geometrică și cere încă verificare în mișcare la importul traseului final de cameră. Dispariția ierbii în transferul către harta PPC este deliberată. Testul nu validează încă un film complet, mișcarea continuă a camioanelor, desenele animate ale panglicilor sau montajul 2D.
'''
(ROOT/'README.md').write_text(readme)
print(json.dumps(summary,indent=2))
