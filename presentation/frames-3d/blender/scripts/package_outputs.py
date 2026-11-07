"""Package the five untouched Cycles stills and 180 rendered frames. Requires Pillow, ffmpeg, ffprobe."""
from pathlib import Path
import json, statistics, subprocess, time
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
BEATS=['storm','where','problems','map','dawn']
for name in BEATS:
    with Image.open(ROOT/'stills'/f'{name}.png') as im:
        assert im.size==(1920,1080),(name,im.size)
frames=sorted((ROOT/'motion'/'frames').glob('*.png'))
assert [p.name for p in frames]==[f'{f:04d}.png' for f in range(1,181)],'Need exactly frames 0001..0180.'
for path in frames:
    with Image.open(path) as im: assert im.size==(1920,1080),path
# Order is storm, where, problems, map, dawn. No text is added to the sheet.
w,h,gap=624,351,16
sheet=Image.new('RGB',(1936,750),'#E7E3DC')
for i,name in enumerate(BEATS):
    row=i//3; col=i%3; x=16+col*(w+gap)+(320 if row else 0); y=16+row*(h+gap)
    with Image.open(ROOT/'stills'/f'{name}.png') as im: sheet.paste(im.resize((w,h),Image.Resampling.LANCZOS),(x,y))
sheet.save(ROOT/'stills'/'contact_sheet.jpg',quality=95,subsampling=0)
cmd=['ffmpeg','-y','-framerate','30','-start_number','1','-i',str(ROOT/'motion'/'frames'/'%04d.png'),'-frames:v','180','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-an',str(ROOT/'motion'/'map_test.mp4')]
t=time.perf_counter(); subprocess.run(cmd,check=True); encoding=time.perf_counter()-t
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_frames:format=duration','-of','json',str(ROOT/'motion'/'map_test.mp4')]))
st=probe['streams'][0]
assert st['codec_name']=='h264' and st['pix_fmt']=='yuv420p' and st['width']==1920 and st['height']==1080
assert st['r_frame_rate']=='30/1' and int(st['nb_frames'])==180 and float(probe['format']['duration'])==6
records=[json.loads(line) for line in (ROOT/'timings.jsonl').read_text().splitlines()]
stills={}
for r in records:
    if r['kind']=='stills': stills[r['beat']]=r
motion={r['frame']:r for r in records if r['kind']=='motion'}
assert set(motion)==set(range(1,181))
ts=[motion[f]['seconds'] for f in range(1,181)]
summary={'stills_seconds':{b:stills[b]['seconds'] for b in BEATS},'motion':{'frames':180,'samples':48,'mean_seconds':statistics.mean(ts),'median_seconds':statistics.median(ts),'min_seconds':min(ts),'max_seconds':max(ts),'render_sum_seconds':sum(ts)},'encoding_seconds':encoding,'ffprobe':probe}
(ROOT/'qa'/'delivery_check.json').write_text(json.dumps(summary,indent=2)+'\n')
rows='\n'.join(f'| {b} | {stills[b]["seconds"]:.3f} |' for b in BEATS)
readme=f'''# Daybreak în Blender

Machetă arhitecturală procedurală, cu 43 de case, depou, camioane cu nacele pliate, stâlpi și fire, nuci fațetați, câmp cu șanțuri, nor de furtună, ploaie, trei socluri și trei trasee cu nouă pini. Geometria și amplasarea sunt sintetice. Nu reprezintă o localitate sau o rețea reală.

Totul se reconstruiește din cod, fără modele descărcate, imagini de fundal sau dependențe de imaginile AI. Sămânța fixă este `270611`. Cele cinci camere și luminile fiecărui cadru sunt salvate în `daybreak.blend`. Fișierul se deschide pe harta completă.

## Livrabile

- `stills/storm.png`, `where.png`, `problems.png`, `map.png`, `dawn.png`, toate 1920×1080.
- `stills/contact_sheet.jpg`, cinci cadre în ordinea brief-ului, fără etichete adăugate.
- `motion/map_test.mp4`, 6 secunde, 30 fps, 180 de cadre, 1920×1080, H.264, yuv420p, fără audio.
- `scripts/build_scene.py`, `render_scene.py`, `package_outputs.py` și `daybreak.blend`.
- `timings.jsonl` păstrează durata fiecărei randări, inclusiv fiecare cadru de animație. `qa/delivery_check.json` conține verificarea finală.

## Comenzi exacte

Rulați din directorul proiectului:

```bash
cd /Users/teo/.t3/worktrees/CyberPunks/Teo-prezentare

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -t 12 -P presentation/frames-3d/blender/scripts/build_scene.py

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak.blend -t 12 -P presentation/frames-3d/blender/scripts/render_scene.py -- --mode preview --beats storm map --width 960 --samples 40

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak.blend -t 12 -P presentation/frames-3d/blender/scripts/render_scene.py -- --mode stills --samples 256

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak.blend -t 12 -P presentation/frames-3d/blender/scripts/render_scene.py -- --mode benchmark --width 1920 --samples 48

/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b presentation/frames-3d/blender/daybreak.blend -t 12 -P presentation/frames-3d/blender/scripts/render_scene.py -- --mode motion --width 1920 --samples 48 --start 1 --end 180

/opt/homebrew/bin/python3.14 -I -B presentation/frames-3d/blender/scripts/package_outputs.py
```

Doar ultimul pas cere Pillow, ffmpeg și ffprobe pe PATH. Blender folosește propriul Python. Randarea refuză trecerea silențioasă pe CPU dacă Metal nu este disponibil. Se pot relua intervale de cadre cu `--start` și `--end`; ambalarea cere secvența completă 0001–0180.

Codarea folosită de script este echivalentă cu:

```bash
ffmpeg -y -framerate 30 -start_number 1 -i presentation/frames-3d/blender/motion/frames/%04d.png -frames:v 180 -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart -color_primaries bt709 -color_trc bt709 -colorspace bt709 -an presentation/frames-3d/blender/motion/map_test.mp4
```

## Setări și durate măsurate

Blender 5.2.1 LTS, Apple M5 Max, Metal GPU cu 32 de nuclee. CPU exclus din dispozitivele Cycles. Randările statice folosesc 256 de eșantioane maxime, prag adaptiv 0,02, denoise, AgX Very High Contrast, expunere −0,5. Animația folosește 48 de eșantioane, denoise și aceeași gestiune a culorilor. Șase ricoșee maxime, patru difuze, trei lucioase. PNG RGB pe 8 biți. Nu există bloom sau text.

Luminile sunt suprafețe mari invizibile camerei. Masa și fundalul continuu sunt o singură suprafață curbată, cu normale calculate pentru a evita o linie de orizont. Materialele albe au un strat local de umbrire pentru contact, calculat din geometrie pe o rază de 0,8 unități, cu patru probe. Modelul are muchii teșite, fațade cu goluri și suprafețe retrase, nu ferestre pictate.

Timpul măsoară apelul de randare, denoise și scrierea PNG; exclude pornirea Blender și încărcarea scenei. Valorile depind de temperatura și încărcarea mașinii.

| Cadru static | Secunde |
|---|---:|
{rows}

Animație: media {statistics.mean(ts):.3f} s/cadru, mediana {statistics.median(ts):.3f} s/cadru, interval {min(ts):.3f}–{max(ts):.3f} s/cadru. Suma celor 180 de randări este {sum(ts):.1f} secunde, adică {sum(ts)/60:.2f} minute. Codarea H.264 a durat {encoding:.2f} secunde.

Proba inițială la 1080p și 48 de eșantioane a indicat aproximativ 18 minute pentru 180 de cadre, sub limita de 25 de minute. Rezoluția și numărul de eșantioane au rămas neschimbate pentru livrare.

## Camere, mișcare și limite

Camerele sunt ortografice pentru aspectul de machetă. În clip, camera urcă și se retrage în spațiul 3D, urmărește continuu centrul cadrului și își lărgește câmpul vizual. Traseele cresc prin geometria curbelor; camioanele urmează lungimea drumului; pinii coboară la atingerea destinației. Mișcarea se calculează determinist în scriptul de randare, fără chei de animație salvate în fișierul blend.

Cadrul `where` izolează depoul prin ascunderea restului satului. Clipul păstrează tot satul vizibil în aceeași poziție și începe cu cele trei camioane de traseu. Nu pornește din imaginea statică cu cinci camioane parcate.

Norul are geometrie unificată, deplasare fină și material de fetru procedural. Nu are fibre individuale. Casele repetă o familie mică de forme. Stâlpul rupt din `storm` rămâne un detaliu mai discret decât norul. Răsăritul păstrează umplere neutră pentru ca modelul să rămână alb; nu colorează tot satul în galben.

Cele cinci imagini finale au fost inspectate vizual pentru text, obiecte de iluminat vizibile, spațiu liber și citirea traseelor. Cadrele de probă și verificările sunt în `qa/`. Clipul a fost verificat prin cadre distribuite pe durata sa, iar ffprobe confirmă formatul și durata.
'''
(ROOT/'README.md').write_text(readme)
print(json.dumps(summary,indent=2))
