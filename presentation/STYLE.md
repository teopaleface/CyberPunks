# Stilul video-ului de 30 de secunde

Video-ul "Tura de mâine" urmează articolul lui leo (@leomeethewoo), "Make your product videos look expensive (Apple Framework)", 25 sep. 2026: https://x.com/leomeethewoo/status/2103529310208606701 . Mai jos sunt regulile lui, rezumate de noi, și felul în care le aplicăm. Orice alegere din video trebuie să se poată justifica de aici.

## Regulile lui leo, pe scurt

1. Intenție în tot. Nimic nu e întâmplător: fontul, fundalul, muzica, culorile au fiecare un motiv. Un brand premium e mai ales ce nu face: fără efecte în plus, fără sunete inutile.
2. Reguli fixe: 3 culori pentru tot video-ul, aceleași fundaluri, aceeași familie de muzică. Publicul simte că "așa trebuia să fie".
3. Întâi designul. Fiecare cadru se desenează static (storyboard), apoi se animă. Principii: un cadru = o idee; fiecare scenă are spațiu să respire; obiectul principal stă în centru; fundalul nu concurează cu el.
4. Animație: mișcări cu easing (nimic liniar) și suprapuse; tranziții fluide între scene (tăietura directă doar dacă mesajul o cere); ritm adaptat: accelerează, încetinește, stă.
5. Muzica alege energia: 60-80 BPM regal/cinematic, 90-110 BPM smooth/cool/effortless, 115-123 BPM elite/kinetic.
6. Sound design minim: dacă un sunet e prea tare, nelalocul lui sau nu ajută la înțelegere, se scoate.

## Ce înseamnă pentru noi

### Povestea, într-o frază

Filmul merge de la noapte la dimineață: seara, 2 milioane de contoare trimit date; un scor singur nu trimite pe nimeni nicăieri; agentul face planul; dimineața echipele pleacă. "Tura de mâine" chiar asta înseamnă.

### Cele 3 culori (aceleași ca în produs)

Filmul folosește culorile consolei "Panou" și ale logoului, ca juriul să vadă un singur produs în film, în demo și în slideuri (decizie 13:25, după alegerea interfeței).

| Culoare | Hex | Ce poartă |
|---|---|---|
| Cerneală | `#0B1622` | Fundalul: cerneala logoului, ca cerul nopții. Niciodată un gol: fiecare cadru are o lume (România noaptea, obiectele, consola, zorii). |
| Hârtie | `#F5F4F0` | Tot textul și acțiunile agentului: traseele, opririle, "Act", bara noastră. Textul secundar: aceeași culoare la 66%. |
| Soare | `#F2A20C` | Doar soarele din logo și zorii de la final. |

Culorile surselor, exact ca în consolă (variantele pentru fundal închis, testate pentru daltonism de firul UI), apar doar pe markerii surselor, cu litera în ei: A contoare `#3B82F0`, B furtună `#B84FC0`, C tensiune `#C4880A`. În produs chihlimbarul înseamnă sursa C, deci filmul nu îl mai folosește pentru acțiunile agentului.

Culorile din fotografii (luminile NASA, imaginile de produs) aparțin lumii, nu interfeței.

Semnul produsului e logoul făcut de firul UI ("răsărit pe traseu": un soare care răsare în spatele traseului unei echipe, cu trei opriri). Apare animat la nume (traseul se desenează, soarele răsare) și pe cartea de final, odată cu zorii.

### Tipografia

- Un singur font, același ca în consolă: Archivo (licență OFL, varianta cu lățime și greutate variabile, fișierele în `video/assets/fonts/`). Are ș și ț cu virgulă (verificat în randare).
- Titluri: 600, 124-136 px, spațiere -3,5%. Afirmații: 600, 84-92 px. Text mic: 450, 34-44 px. Minim 28 px pentru orice text de citit.
- Cifrele mari (0,87, cifra față de baseline) sunt late (lățime 112%), ca cifrele zilei din consolă.
- Doar litere mici la început de propoziție (sentence case), fără majuscule pe etichete, fără supratitluri, fără numerotări decorative.
- "Perceive, Estimate, Decide, Act" rămân în engleză: sunt cuvintele din tema PPC, juriul le recunoaște.

### Mișcarea

- Intrări: `expo.out` sau `power4.out`, 0,5-0,8 s. Cuvintele intră cu blur (10 px → 0), la 0,067-0,12 s unul după altul, fără alunecare în sus.
- Camera: `power2.inOut`, 1,5-5 s, împingeri lente (scara 1,00 → 1,06).
- Ieșiri: `power3.in`, cu 40-50% mai scurte decât intrările.
- Un titlu ajuns pe loc stă nemișcat. Mișcarea trece la următorul element sau la lumea din spate.
- Tranziții, fiecare cu o cauză pe ecran: zoom printr-o lumină (harta → scorul), obiectul devine lumea (scorul → prima oprire a traseului din logo → numele), schimb cu blur pe aceeași scenă, whip între cele trei semnale, inundație de culoare (noaptea → zorii, la final).
- Ritmul: încet la început (2 cadre de câte 5 s), repede la mijloc (semnalele, 1,25 s fiecare), încet pe hartă (6,25 s), oprire la "Nu sunt sigur", final ținut 2,5 s.

### Muzica și sunetul

- Muzică originală, compusă în cod (fără sample-uri), 96 BPM, 4/4, o măsură = 2,5 s, 12 măsuri = 30 s. "Smooth, cool, effortless": încredere calmă, nu EDM, nu epic.
- La 30 de cadre pe secundă, fiecare măsură începe pe un cadru întreg (0, 75, 150 ... 900).
- Fără voce. Fără efecte sonore decorative; cel mult un swell discret înainte de nume, dacă ajută.
- Mix final: -16 LUFS, vârf real -1 dBTP.

### Ce interzicem (BANNED)

- Un gol negru cu elemente mici plutind la mijloc. Fiecare cadru are o lume.
- Glow, bloom, neon, particule decorative, lens flare adăugate în cod, gradienți mov sau albaștri, carduri de sticlă.
- Majuscule pe etichete, supratitluri, "01 / 02", chips-uri în formă de pastilă, etichete în colțuri ca decor.
- Trei carduri pe un rând, grile de KPI, titlu peste o captură întunecată.
- Totul intră deodată; fiecare element intră cu fade și alunecare în sus.
- Text care se mișcă în timp ce e citit.
- Logo lipit în colț.
- Cifre care nu vin din `reports/`.
- Chihlimbarul pe altceva decât soarele din logo, zorii și sursa C.

### Transparență (cerută și de PPC, vezi `memory/08-ppc-workshop-ai.md`)

- Pe cadrele cu imagini generate cu AI: eticheta discretă "Imagine generată cu AI".
- Pe consolă: "Date sintetice" acolo unde datele sunt sintetice.
- Ziua demo-ului, 8 iulie 2025, e reală: cod roșu ANM de vijelii în Banat, caniculă și 881 W/m² la prânz în București (surse în `docs/research/B.md`).
- Harta de noapte: "NASA Black Marble 2016". Granițele: geoBoundaries (CC BY 4.0).
- Toate sursele și uneltele sunt în `CREDITS.md`.
