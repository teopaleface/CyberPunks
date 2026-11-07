# C pe o pagină: tensiunea prea mare pe posturile cu prosumatori

Pentru prezentare și pentru interfață. Toate cifrele vin din scripturi (comanda e lângă fiecare). Posturile, rețelele și prosumatorii sunt SINTETICI; vremea e reală.

## Problema, în cifrele publice

- România: 385.791 de prosumatori, 4.281,86 MW, 151.040 cu stocare (ANRE, 31 aug. 2026). **Ilfov e primul județ din țară: 21.647 de prosumatori, 303,81 MW.** Toată zona e a Rețele Electrice.
- La prânz tensiunea urcă în rețeaua de joasă tensiune; peste 1,10 pu (253 V) invertoarele se opresc singure (Ord. ANRE 132/2020, Tabelul 2P). Prosumatorii pierd energie, distribuitorul primește reclamații (70 lei compensație pe reclamație întemeiată, Ord. ANRE 46/2021).
- Problema nu e în portofoliul AI declarat de PPC.

## Ce face agentul pentru C

1. **Estimează** pentru fiecare post și pentru mâine tensiunea maximă (P10, P50, P90, oră cu oră) și probabilitatea depășirii, cu un model antrenat pe simulări fizice.
2. **Alege soluția cea mai ieftină care ajunge**, din scara de soluții simulată pe rețeaua postului: 3 case mutate pe altă fază, o treaptă de priză, mesaje de grup, baterii, limită de export, post nou.
3. **Spune de ce**: motivele modelului în cuvinte simple, efectul fiecărei soluții în pu, de ce nu una mai ieftină.
4. **Trimite la om** ce nu e sigur (date greșite, rețea nouă, prognoză incertă lângă prag).

## Cifrele (rețele nevăzute × luni nevăzute, 324.000 de zile-post; `make c-eval`)

| | Modelul C | Metoda simplă (soare × kW/kVA) |
|---|---|---|
| Eroarea medie la tensiunea maximă | **0,0054 pu** (circa 1,2 V) | 0,0227 pu (circa 5,2 V) |
| Depășiri prinse (recall) / alarme corecte (precizie) | **86% / 87%** | 26% / 60% |
| PR-AUC pe depășiri | **0,95** | 0,43 |
| Intervalul P10-P90 conține valoarea reală | **82%** (ținta 80%) | 79%, dar de 4 ori mai lat |
| 300 de posturi, o zi | **0,07-0,09 s** | calculul de rețea: 62-87 s și rețeaua detaliată a fiecărui post |

- Pe ziua demo (8 iulie 2025): simularea fizică dă 16 posturi peste 1,10 pu; modelul le găsește pe toate 16, plus 2 aflate la 1,097 pu.
- Ablație: fără datele de topologie (din GIS) eroarea se dublează și depășirile nu mai sunt prinse. Argument direct pentru GIS-ul nou al Rețele Electrice.

## Ziua demo: 8 iulie 2025 (`make c-predict`)

- Caniculă, cer senin, 956 W/m² pe panou la prânz, 35 °C. 300 de posturi, 33 de lucrări C, 18 posturi cu probabilitate peste 50%.
- Scara de soluții: 8 × o treaptă de priză, 4 × 3 case mutate pe altă fază, 2 × limită de export, 19 mesaje de grup.
- Exemplu (PT-1252, Popești-Leordeni): P90 1,113 pu după model, 1,133 pu cu dezechilibrul de faze estimat. O treaptă de priză singură îl lasă la 1,109 pu, 3 case mutate pe altă fază la 1,115 pu; împreună îl aduc la 1,092 pu, pentru 1.956 lei. Mesajele (−0,0018 pu la 10% participare) și bateriile (−0,0044 pu) nu ajung singure.
- Oferte de baterii pentru PPC Energie: 113 prosumatori pe 14 posturi, recuperare mediană de circa 5 ani cu grantul Casa Verde Baterii 2026; bateria încărcată la prânz se descarcă seara, în orele de deficit 18-22 (`reports/C/oferte_baterii.md`).
- Mâine, cu prognoza reală de noiembrie: pe 8 nov. (duminică senină și rece, 730 W/m²) 7 posturi cu risc peste 50%, nicio echipă, doar mesaje și urmărire, pentru că în afara sezonului o vizită nu se justifică; pe 9 nov. (înnorat 78%, 484 W/m²) niciun post peste 50%, nicio echipă, 9 posturi urmărite și 2 cazuri nesigure la om. Explicația spune de ce: soarele de noiembrie e slab. Agentul explică de ce: panourile reci produc aproape cât vara, iar duminica consumul e mic.

## Postul pentru legătura cu bilanțul: PT-1082 (1 Decembrie, sintetic)

- Bilanțul pe post (`A-20250708-PT-1082`) găsește dezechilibru pe faze: circa 77% din case pe o fază, pierderi pe cabluri de 2,9 ori normalul.
- C (`C-20250708-PT-1082`) folosește constatarea în scara de soluții: P90 1,138 pu (cu dezechilibrul). Mutarea a 3 case −0,011 pu (încredere medie, susținută de bilanț), o treaptă de priză −0,025 pu, ofertele de baterii −0,008 pu: împreună 1,095 pu, pentru 1.966 lei. Fără mutarea caselor, combinația ieftină nu ajunge sub 1,10.
- PT-1269 (propus de bilanț): aceeași legătură, dar acolo problema e mai ales cantitatea de panouri; mutarea caselor e prima treaptă dintr-o soluție cu baterii și limită de export (12.439 lei).

## Figuri (`reports/C/figures/`)

- `pred_vs_sim.png`: tensiunea prezisă față de simularea fizică, model și metoda simplă, pe rețele nevăzute.
- `series_demo-vara.png`: un post pe 8 iulie 2025, oră cu oră: intervalul P10-P90, P50 și simularea fizică, cu limita de 1,10 pu.
- `reliability.png`: probabilitatea prezisă față de frecvența reală (modelul calibrat stă pe diagonală).
- `mae_by_topology.png`: eroarea pe fiecare rețea lăsată deoparte la antrenare.
- `ladder_demo-vara_PT-1252.png`: scara de soluții pentru un post: ce aduce tensiunea sub 1,10 pu și cât costă (efecte simulate).

## Mai multe

- Cum s-a construit și ce date: `docs/data/C.md`, `docs/research/C.md`.
- Fișa modelului: `reports/C/model_card.md`. Analiza erorilor: `reports/C/error_analysis.md`.
- Investiții (posturile de modernizat, ordonate): `reports/C/investitii.md`.
- Cereri de racordare: `uv run python -m cyberpunks.c_prosumatori.connection --post PT-1020 --kwp 25`. Răspunde „aprobat”, „aprobat cu limită de injecție” sau „studiu”, cu explicație, iar regula simplă de azi (3%) e pusă alături.
