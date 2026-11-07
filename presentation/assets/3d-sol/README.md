# Obiecte 3D pentru Tura de mâine

Modele originale, modelate procedural de un agent AI, gpt-6.1-sol, în Blender 5.2.1. Geometria, materialele și luminile sunt create prin `bpy`. Nu sunt folosite modele, texturi sau alte materiale descărcate. Imaginile `../gen3d/obj_*.png` au fost consultate vizual pentru formă și culori; nu sunt proiectate pe plane.

## Fișiere

Pentru fiecare nume `meter`, `transformer`, `solar`, `storm`, `helmet`:

- `<name>_hero.png`: 1024 × 1024, PNG RGBA, fundal transparent, vedere din trei sferturi.
- `<name>_spin/0000.png` până la `0029.png`: exact 30 de cadre de 512 × 512, PNG RGBA.
- `<name>_spin_sheet.png`: 3072 × 2560, PNG RGBA, 6 coloane × 5 rânduri. Ordinea începe în stânga sus și continuă de la stânga la dreapta.
- `<name>_render_metrics.json`: timpii măsurați pentru fiecare randare și datele încadrării.

Fișiere comune:

- `render_objects.py`: toate cele cinci modele, materialele, studioul și randarea.
- `prepare_assets.py`: verificări, asamblarea foilor și previzualizarea video.
- `contact_white.png`: toate cele cinci imagini principale pe alb, 1800 × 1320.
- `spin_review.png`: toate cele 150 de cadre pe alb, 2400 × 1760.
- `turntable_white.mp4`: previzualizare pe alb, H.264, 1800 × 1100, 30 fps, 3,333 secunde, fără sunet. Repetă mișcarea de două ori, cu o pauză pe unghiul final. PNG-urile și foile originale păstrează transparența.
- `verification.json`: rezultatul verificărilor pentru toate randările și foile.
- `3d-sol.zip`: arhiva cu toate fișierele de mai sus și acest README.

## Comenzi exacte

Comenzile de mai jos reproduc setul final în acest director. Prima comandă suprascrie randările cu aceleași nume. Python-ul folosit aici are deja Pillow 12.0 și NumPy. FFmpeg este necesar doar pentru previzualizarea MP4.

```sh
/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -t 8 -P "/Users/teo/.t3/worktrees/CyberPunks/Teo-prezentare/presentation/assets/3d-sol/render_objects.py" -- --mode all
python3 "/Users/teo/.t3/worktrees/CyberPunks/Teo-prezentare/presentation/assets/3d-sol/prepare_assets.py" --video
```

Doar un obiect, cu aceleași setări:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -t 8 -P "/Users/teo/.t3/worktrees/CyberPunks/Teo-prezentare/presentation/assets/3d-sol/render_objects.py" -- --objects helmet --mode all
```

`--mode hero` produce numai imaginile principale; `--mode spin` produce numai secvențele. `--device cpu` permite randarea fără Metal, dar timpii vor fi diferiți. Fără `--video`, a doua comandă verifică și asamblează toate imaginile fără să apeleze FFmpeg.

## Randare și mișcare

- Cycles, Metal, Apple M5 Max GPU cu 32 de nuclee. Denoising OpenImageDenoise.
- 64 de eșantioane pentru imaginile principale, 32 pentru cadrele animației. Adaptive sampling 0,025, maximum 6 ricoșeuri de lumină.
- Film Transparent activ, PNG RGBA de 8 biți, alpha drept, fără fundal sau plan de sol. Umbrele dintre piesele obiectului sunt calculate în 3D.
- Color management Standard, look None, exposure −0,20, gamma 1. Paleta sRGB este convertită în valori liniare pentru materialele Blender.
- Aceeași cameră ortografică pentru toate obiectele, poziție `(7, -11, 6.7)`, orientată spre origine, scară 5,6. Aceleași patru lumini de studio albe și același mediu alb cu intensitate 0,8.
- Luminile au 100 W în stânga sus, 50 W în dreapta, 100 W din spate și o lumină verticală de 30 W pentru reflexii.
- Rotație reală în jurul axei Z, de la 120° la 0°. Înclinarea pe X trece de la −6° la 0°, iar cea pe Y de la 9° la 0°.
- Accelerația și viteza sunt zero la început și la sfârșit, prin interpolare `6t⁵ − 15t⁴ + 10t³`.
- Cadrul 29 are exact poziția 3D, unghiul, camera și lumina imaginii principale. Rezoluția și numărul de eșantioane diferă.
- Imaginile principale ocupă aproximativ 80% din latura cadrului. Încadrarea verifică geometria evaluată în toate cele 30 de poziții. Silueta rămâne centrată. Numai casca are și o compensare de scară, de cel mult 12,1%, în unghiurile în care cozorocul este mai lat.

În montaj, folosește întreaga suprafață de 512 × 512 pentru fiecare cadru. Decuparea automată separată a cadrelor poate schimba poziția și scara. Secvența are o secundă la 30 fps; ultimul cadru poate fi ținut cât cere montajul.

## Timpi măsurați

Timpii includ apelul de randare și scrierea PNG-ului. Sunt din ultima randare completă, nu estimări.

| Obiect | Imagine principală, s | Medie pe cadru de animație, s | Cel mai lent cadru de animație, s |
|---|---:|---:|---:|
| meter | 4,25 | 0,64 | 1,01 |
| transformer | 3,59 | 0,64 | 0,83 |
| solar | 2,73 | 0,78 | 1,15 |
| storm | 4,12 | 0,72 | 1,04 |
| helmet | 4,93 | 0,95 | 1,58 |

Cele 155 de randări au luat aproximativ 132 de secunde cumulat, plus construirea geometriei și asamblarea fișierelor. Pornirea la rece sau alte sarcini pe GPU pot schimba timpii.

## Verificare

`verification.json` confirmă 155 de randări și 5 foi. Toate au dimensiunea cerută și patru canale RGBA. Toate colțurile au alpha 0. Niciun pixel al obiectului nu atinge marginea vreunui cadru. Există pixeli complet opaci și pixeli de tranziție la contur.

Marginea liberă minimă, măsurată pe alpha, este 43 px pentru contor, 35 px pentru transformator, 50 px pentru solar, 37 px pentru furtună și 35 px pentru cască. Fiecare dintre cele 150 de zone din foile de cadre este identică pixel cu pixel cu PNG-ul original.

Imaginile principale micșorate la 512 și cadrele 29 diferă în medie cu mai puțin de 0,65 niveluri RGB din 255 pe canal. Diferența vine din rezoluție, filtrare și numărul de eșantioane.

Contactul pe alb și toate cele 150 de cadre au fost inspectate vizual. Au fost corectate zonele albe arse, rama prea dreptunghiulară a ecranului, rostul capacului contorului și încadrarea obiectelor în timpul rotirii. Nu se văd fețe poligonale pe suprafețele rotunde la dimensiunea livrată.

## Evaluare proprie

- Contorul are o siluetă clară, ramă rotunjită, buton metalic și ecran albastru. Fața este mai plată și mai simplă decât în referință; ecranul rămâne fără text, ca în referință.
- Transformatorul are cele mai multe detalii de construcție: radiatoare, izolatoare ceramice, prezoane filetate, coliere și suport diagonal. Finisajul betonului este discret. Este o interpretare vizuală, nu un model tehnic al unui echipament PPC.
- Panoul solar are celule separate, conductori fini, prinderi și țigle cu volum. Soarele este o sferă lucioasă. Acoperișul este mai subțire și mai deschis în lateral decât în referință; la 512 px, detaliile fine ale celulelor se pierd parțial.
- Norul are un singur volum neted, cu baza prună și un fulger alb cu grosime reală. Arată mai mult ca o pictogramă lucioasă decât ca un nor natural. Pe profil, fulgerul se citește mai puțin, apoi devine clar pe măsură ce se rotește spre cameră.
- Casca are o carcasă goală, cozoroc curbat, două nervuri și bandă amber continuă. Forma și reflexiile sunt curate. Suspensia interioară și microtextura benzii sunt simplificate față de referință.

Nu s-a făcut comparația cu rezultatul celuilalt model. Toate fișierele create pentru acest set sunt în `3d-sol/`; în afara acestui director a fost adăugată numai mențiunea cerută în `../gen/PROMPTS.md`. Nu s-au folosit comenzi git.
