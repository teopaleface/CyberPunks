# Tura de mâine: obiecte 3D pentru film

Cinci obiecte modelate procedural în Blender 5.2.1 de gpt-6-astra. Material AI-made: geometria, materialele, luminile și animația au fost construite de un agent AI în Blender. Fără modele, texturi sau medii HDRI descărcate. Imaginile `../gen3d/obj_*.png` au fost consultate vizual, nu proiectate pe obiecte.

## Fișiere

Pentru fiecare nume `meter`, `transformer`, `solar`, `storm`, `helmet`:

- `<nume>_hero.png`: 1024 × 1024, PNG RGBA transparent, vedere de trei sferturi.
- `<nume>_spin/0000.png` până la `0029.png`: 30 de cadre de 512 × 512, PNG RGBA transparent.
- `<nume>_spin_sheet.png`: 3072 × 2560, 6 coloane × 5 rânduri. Cadrele sunt copiate fără redimensionare, în ordinea rândurilor.
- `<nume>.blend`: scena editabilă, cu geometrie, materiale procedurale, cameră, lumini și animație.
- `<nume>_preview.webp`: previzualizare animată transparentă. Ține ultimul cadru încă 700 ms; cadrele PNG nu conțin această pauză.

Fișiere comune:

- `contact_white.png`: cele cinci imagini hero, pe alb, cu etichete; 2560 × 586.
- `turntables_white.webp`: previzualizarea celor cinci animații pe alb.
- `build_render.py`: construiește geometria și randează.
- `assemble_verify.py`: construiește planșele și verifică imaginile.
- `inspect_geometry.py`: verifică scenele 3D și camera comună.
- `verification.json`: verificările PNG, încadrarea, comparația ultimului cadru cu hero și timpii măsurați.
- `scene_verification.json`: numărul de obiecte și vârfuri, cele 30 de poziții și configurația comună de studio.
- `<nume>_timing_all.json`: durata fiecărei randări finale, inclusiv scrierea PNG.

## Reproducere

Comenzile de mai jos scriu numai în acest director. Refac fișierele cu aceleași nume. Blender folosește Metal pe GPU dacă este disponibil; altfel folosește CPU. Scriptul de asamblare necesită Pillow. Pe calculatorul de lucru a fost folosit Python 3.14 cu Pillow 12.2.0.

```bash
cd /Users/teo/.t3/worktrees/CyberPunks/Teo-prezentare/presentation/assets/3d-astra

/Applications/Blender.app/Contents/MacOS/Blender -b -t 8 -P build_render.py -- --mode all

/opt/homebrew/bin/python3.14 -I -B assemble_verify.py

/Applications/Blender.app/Contents/MacOS/Blender -b -t 8 -P inspect_geometry.py
```

Pentru un singur obiect:

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b -t 8 -P build_render.py -- --mode all --objects meter
```

Pentru imaginile hero, fără animații:

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b -t 8 -P build_render.py -- --mode heroes
/opt/homebrew/bin/python3.14 -I -B assemble_verify.py --heroes-only
```

## Randare și montaj

- Cycles pe Apple M5 Max, GPU Metal cu 32 de nuclee.
- Hero: maximum 96 samples. Animații: maximum 32 samples. Adaptive sampling 0,025, minimum 16 samples. Denoising OpenImageDenoise.
- PNG RGBA, 8 biți pe canal. Film Transparent activat, fără plan de fundal sau umbră desenată în PNG.
- Color management Standard, Look None, exposure 0, gamma 1. Culorile din paletă sunt convertite din sRGB în valorile liniare folosite de shader.
- Cameră ortografică fixă la 6, -11, 4,8, orientată spre origine, ortho scale 4,8.
- Aceleași patru lumini și același mediu neutru pentru toate obiectele. Key 135 W, fill lateral 75 W, rim 100 W, fill frontal 85 W; world strength 0,40.
- 30 fps, cadre 0–29. Rotație de 120° în jurul axei verticale, cu pornire și oprire lentă prin curba `6u^5 - 15u^4 + 10u^3`. Înclinarea X variază de la 11° la 2°, Y de la -12° la -4°.
- Obiectul este translatat puțin în planul imaginii ca silueta să rămână centrată. Camera și luminile rămân fixe. Scara rămâne constantă în animația fiecărui obiect.
- Cadrul 29 are exact orientarea, poziția și scara din hero. Cele două rezoluții și niveluri de sampling produc mici diferențe de pixeli, nu o schimbare de unghi.
- Secvența este o intrare cu oprire, nu o rotație de 360° și nici o buclă fără salt. La 30 fps durează o secundă. Pentru montaj se poate ține cadrul 29 cât este necesar.
- Importă secvențele și planșele cu alpha straight. Nu elimina albul sau negrul printr-un filtru de culoare. Fundalul alb există numai în previzualizările numite `white`.

## Autoevaluare vizuală

- Contor: carcasă rotunjită, ecran albastru, capac separat, șuruburi și spate modelat. Este simplificat deliberat, fără cifre sau marcaje.
- Transformator: modelul cu cele mai multe detalii, cu aripioare rotunjite, trei izolatoare, cleme și stâlp din beton. Detaliile mici se pierd la scara unui obiect mic în film. Este o reprezentare stilizată, nu un model tehnic pentru construcție.
- Solar: celule distincte, ramă metalică, țiglă cu volum, cleme și soare sferic. Canelurile celulelor sunt mai discrete decât într-o fotografie apropiată.
- Furtună: volum continuu, degradeu prune și fulger extrudat. Este cel mai stilizat obiect; lobii norului sunt mai pronunțați decât în referință.
- Cască: coajă cu grosime, nervuri, cozoroc, bandă amber și suspensie interioară. Suspensia este simplificată, iar forma este puțin mai compactă decât în referință.

Am verificat contactul pe alb și am corectat reflexiile care spălau panoul solar, îmbinarea vizibilă de la baza căștii, banda ondulată și intersecția norului cu fulgerul. Nu am verificat integrarea în montajul final al filmului.
