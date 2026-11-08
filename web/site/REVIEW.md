# Revizuire anti-slop · Bilanț pe post

7 nov. 2026. Revizuire după „Ghid AI: arhitectură web fără AI slop” și regulile taste-skill, verificată cu `inspect.mjs` (Chrome, 1440 / 768 / 390 px).

## Brief și presupuneri

Utilizatorul (juriul SmartHack și dispecerii PPC) vine ca să vadă unde se pierde energia în rețea, cât costă și cine trebuie să meargă acolo.

- Totul este public deocamdată; contul (Supabase) păstrează aprobările și profilul.
- Datele sunt simulate; site-ul spune asta.
- Brief-ul cere explicit: navbar și butoane liquid glass, gradient sub hero, beam de lumină, footer halftone. Acestea câștigă în fața regulilor generale (vezi excepțiile).

## Sitemap

```
/                 landing, un ecran pe secțiune (scroll care sare din ecran în ecran)
/bilant           funcția: bilanțul pe post
/diagnostic       funcția: de ce lipsește energia (cu sidebar pe cauze)
/clasament        funcția: clasamentul în lei
/agent            funcția: agentul și jurnalul
/intra            intrare / cont nou / resetare parolă
/app              aplicația, cu serviciile în sidebar:
  /app            prezentare
  /app/harta      harta posturilor (Ploiești)
  /app/posturi/:id pagina unui post
  /app/echipe     lista echipelor, cu aprobare (salvată în cont)
  /app/jurnal     jurnalul deciziilor, filtru după verdict
  /app/cont       profil, echipă, ieșire din cont
```

Navbarul este același pe toate paginile: Bilanț, Diagnostic, Clasament, Agent + „Intră în cont” / „Contul meu”.

## Tokens

- Culori: fundal `#000000`, suprafețe `#0b0b0c` / `#141416`, text `#ffffff`, accent `#ff7a1a`; semantice: succes `#4ade80`, avertizare `#facc15`, eroare `#ff5a36`.
- Tipografie: Unbounded (titluri), Geist (text). Titluri −2% (titlul hero peste 64 px: −2%), text 17 px / 1,55.
- Rază: 16 px pe panouri, complet rotund pe butoane.
- Iconuri: Lucide, grosime implicită 2 px. Niciun emoji.
- Mișcare: 150 / 200–300 ms pe feedback, 450 ms pe intrarea secțiunilor, aceeași curbă `cubic-bezier(.22,1,.36,1)`.

## Registrul de excepții

| ID | Regula | De ce rămâne |
| --- | --- | --- |
| C3 | Glassmorphism | Brief-ul cere navbar și butoane CTA liquid glass. Doar acolo; panourile sunt opace. |
| C1 | Gradienți | Regula a fost ridicată (7 nov., decizia echipei). Folosiți cu măsură: sub hero, pe sticla butoanelor, în graficele cu serii și pe panoul „Cum funcționează”. |
| — | Străluciri (glow) | Tema cerută e lumina/energia: beam-ul din hero și reveal-ul siglei. Strălucirile decorative de pe carduri, bare și puncte au fost scoase. |
| V2 | Textură halftone | Footer-ul halftone e cerut explicit în brief. Granulația decorativă de peste footer a fost scoasă. |
| T1 | Font „la modă” | Unbounded e lat și tehnic, ales pentru tema futuristă cerută; folosit doar pe titluri. |
| M1 | Durate peste 300 ms | Intrarea secțiunilor (fade de sus în jos) e cerută în brief; 450 ms, deplasare 16 px. Feedbackul pe controale rămâne 150–300 ms. |
| H3 | Linii | Doar în tabele reale (clasament, jurnal, diagnostic). |
| — | Spațiu gol între secțiuni | Brief-ul cere o singură secțiune pe ecran, centrată, cu același spațiu sus și jos; asta produce benzile goale pe care inspectorul le semnalează. |
| — | `prefers-reduced-motion` | Oprit pentru demo (Windows-ul de prezentare are animațiile dezactivate). Se pornește din `src/lib/motion.ts`. |

## Raport de auto-revizuire

Iterații rulate: 3

| ID | Rezultat | Dovadă | Acțiune |
| --- | --- | --- | --- |
| C1 | EXCEPȚIE | hero, butoane glass | păstrat, cerut |
| C2 | DA | paleta de mai sus; scala de culori doar în grafice și pe hartă | — |
| C3 | EXCEPȚIE | navbar, butoane | păstrat, cerut |
| I1 | DA | niciun emoji | — |
| I2 | DA | iconuri Lucide monocrome, fără cercuri colorate | — |
| T1 | EXCEPȚIE | Unbounded pe titluri | justificat |
| T2 | DA | −2% pe titluri (era −3,5%) | redus |
| T3 | DA | fără italic | — |
| T4 | DA | fără monospace; cifre tabulare în Geist | — |
| T5 | DA | fără eyebrows; etichetele de deasupra cifrelor mutate dedesubt | reparat |
| T6 | DA | „Vezi unde se pierde energia” fără punct | reparat |
| H1 | DA | o cifră sau un titlu dominant pe ecran | — |
| H2 | DA | panouri separate prin ton, fără borduri | — |
| H3 | EXCEPȚIE | linii doar în tabele | — |
| H4 | DA | fără pastile decorative; „probabil” e text | — |
| H5 | DA | fără numerotare 01/02 | — |
| H6 | DA | fără badge-uri decorative | — |
| H7 | DA | o rază (16 px) + butoane rotunde | rotunjirile de 24 px reduse |
| V1 | DA | o singură idee pe grafic | — |
| V2 | EXCEPȚIE | footer halftone | granulația scoasă |
| V3 | DA | navigare în limbaj natural | — |
| X1 | DA | titluri scurtate la ≤ 2 rânduri | reparat |
| X2 | DA | „Azi: 4 cazuri, 2.958 lei pe lună în joc” în loc de „Bine ai revenit” | — |
| S1 | DA | formulare și liste: încărcare, gol, eroare, succes, dezactivat | adăugat |
| M1 | EXCEPȚIE | intrări 450 ms | justificat |

Teste: 5 secunde DA · Eliminare DA · Accent DA (acțiuni, stări active, date) · Iconuri DA · Stări DA · Mișcare DA, cu excepția notată

Modificări făcute în revizuire:
- „SmartHack 2026 …” scos din hero și din footer; punctul din titlul hero scos.
- Soarele din hero coborât ca să nu acopere butoanele.
- Strălucirile decorative și granulația scoase; colțurile unificate la 16 px.
- Titluri scurtate („Cum funcționează”, „Demo pe date publice”, „Încearcă pe rețeaua ta”).
- Animațiile de intrare scurtate (0,9 s → 0,45 s, fără blur).
- Tile-urile ascunse din banda de ecrane nu mai ies din pagină.
- Harta trecută pe OpenStreetMap (CARTO cerea cheie).

Probleme rămase deschise:
- Nicio fotografie reală pe pagină; imaginile sunt fragmente de interfață și desene în cod. O fotografie a unui post de transformare ar ajuta.
- 14 mărimi de font pe landing (ghidul recomandă 5–6); majoritatea vin din grafice și din fragmentele de aplicație.

## Revizuirea 2 (7 nov., după branch-ul `design` din teopaleface/CyberPunks)

- Produsul se numește Daybreak; antetul arată doar cuvântul, fără semn grafic (logourile cu soare au fost respinse).
- Toate cifrele vin din rularea reală a agentului (`outputs/demo`, scenariul demo-vara, 8 iulie 2025), extrase cu `scripts/extract-daybreak.py`. Simularea veche a fost ștearsă.
- Regulile de scriere ale echipei: fără „·” între meta, fără „→” lipit de butoane, etichete „Date sintetice” și „Simulare pe date publice, gândită pentru datele PPC”.
- Culorile surselor din consola echipei: A albastru, B mov-prună, C chihlimbar; markerii poartă și litera.
- Aplicația (`/app`) arată fiecare criteriu al juriului: plan și valoare (idee), modele față de reper (ML), hartă cu trasee și decizii (agent), coada pentru om și testul de robustețe (robustețe), pagina fiecărei lucrări cu factori, cazuri asemănătoare, regulă și urmărire (explicabilitate).
