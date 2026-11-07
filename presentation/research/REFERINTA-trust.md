# Filmul de referință: ce face și cum îl refacem pentru "Tura de mâine"

Referința dată de Teo la 13:45: `trust_replica_A_audio_original_h264.mp4` (o replică a unui film Trust Wallet, "Meme trading is instant", din stilul echipei lui leo). Fișierul nu intră în git (e al lor); aici e doar analiza, cu cifrele măsurate. Teo: "prea banal, prea simplu, nu e așa ușor de văzut, culori nașpa; cel puțin la fel de șmecher ca asta".

Luăm gramatica (ritm, tipografie, culori pe roluri, mișcare, tranziții), nu conținutul lor.

## Ce am măsurat (comenzile sunt la final)

| Ce | Valoare |
|---|---|
| Format | 1920×1080, 30 fps, 21,04 s (631 de cadre), H.264 High, AAC 44,1 kHz |
| Tăieturi dure | doar 2 în 21 s: la 13,83 s (spre "Slide to Buy") și la 15,67 s (pastila neagră acoperă tot, 6 cadre) |
| Restul | o singură mișcare continuă: obiectele se transformă unele în altele |
| Lumina imaginii | luma 186,5 din 255 (foarte luminos), saturație 0,012 (aproape fără culoare), contrast 29 |
| Fundal | alb pur `#FFFFFF` 15,7 s, apoi negru `#010101` 5,3 s |
| Culori | negru pentru text; un singur albastru electric (aprox. `#0000F0`) pe cuvântul-cheie "instant"; verde (aprox. `#108050`) pentru acțiunea reușită (cumpără, grafic); roșu doar pe butonul "Sell" |
| Text | uriaș și centrat: "Meme trading" are 181 px înălțime de cerneală (corp de aprox. 180 px), 65% din lățimea cadrului; textele de final au 106-134 px; un singur rând, mereu |
| Muzica | aprox. 134 BPM, energică; loudness -8,7 LUFS (foarte tare, pentru rețele sociale) |
| Pauze | 10 momente ținute pe loc, de 0,5-2 s; ultimul (logoul) 2 s |

## Firul filmului, secundă cu secundă

| Timp | Ce se vede | Mișcarea |
|---|---|---|
| 0,0-1,6 | "Meme" → "Meme trading" → "is" → "is now" | cuvântul pornește mic și crește brusc (zoom din 20% în 100%, cu frână lungă); cuvântul nou se adaugă, rândul se recentrează lin; cuvintele se schimbă pe bătăi |
| 1,6-2,6 | "instant" în albastru, monede 3D care intră din margini | literele apar cu un gradient care le măture; monedele 3D intră rotindu-se, cu blur de mișcare, la adâncimi diferite (una mare în prim-plan) și se așază |
| 2,6-3,6 | cuvântul se stinge, monedele zboară în aplicație | "obiectul devine lumea": monedele se micșorează și ajung exact pe iconițele din lista aplicației, care apare în spate |
| 3,6-5,3 | ecranul aplicației (fără ramă de telefon, doar ecranul rotunjit, cu umbră moale) | lista urcă, apare tastatura; camera urmărește |
| 5,3-6,3 | butonul "Paste", uriaș, pe alb | ținut 0,6 s, apoi apăsat (se micșorează, devine verde pal) |
| 6,3-7,3 | butonul se strânge într-un punct verde, punctul trage după el linia graficului | butonul → punct → grafic → pagina monedei (camera se retrage) |
| 7,3-10,6 | pagina monedei: graficul se schimbă (1D → 1W), derulare la "Buy", apăsare | ecranul pornește mare și se micșorează, apoi derulează |
| 10,6-13,8 | suma se tastează: $0 → $1 → $10 → $100 | cifrele apar pe bătăi, cu cursor |
| 13,8-15,0 | "Slide to Buy", uriaș; butonul verde alunecă | camera urmărește butonul, care rămâne aproape în centru; textul e acoperit pe măsură ce trece |
| 15,0-15,7 | "Buying" → "Bought ✓" în pastila de sus | starea se schimbă, prețul urcă |
| 15,7 | pastila neagră crește și acoperă tot cadrul | tranziția spre final: obiectul devine fundalul |
| 15,9-21,0 | pe negru: "meme trading" → "on Trust Wallet" → "built for speed" → logoul | fiecare frază pornește mică și crește; ținute 1,1-2 s; logoul 2 s |

## Ce îl face "șmecher" (și ce lipsea filmului nostru)

1. **Se vede de departe.** Alb pur și negru, text de 150-190 px, un rând. Al nostru: fundal închis, text de 84-136 px, culori stinse.
2. **O singură culoare vie pe ecran**, pe ce contează. Restul e alb, negru și gri.
3. **Obiecte 3D care zboară** în jurul cuvântului-cheie și apoi devin parte din produs.
4. **Produsul e eroul**: interfața reală, mare, decupată, cu butoane apăsate la scară uriașă (Paste, Slide to Buy) și cifre care se tastează.
5. **Nicio tăietură gratuită**: buton → punct → grafic → ecran; pastila → fundalul negru.
6. **Ritm rapid** (134 BPM), cu câte o schimbare pe aproape fiecare bătaie, apoi un final calm pe negru.

## Cum îl aplicăm la "Tura de mâine" (film nou, 30 s, 120 BPM)

- **Culori.** Fundal alb `#FFFFFF`, text în cerneala produsului `#0B1622`, finalul pe aceeași cerneală. O singură culoare vie a filmului: soarele din logo `#F2A20C`, ca formă (soarele care răsare în spatele cuvântului), nu ca text. În interfață rămân culorile consolei (A albastru, B prună, C chihlimbar, "la om").
- **Text.** Archivo, 600-700, 150-190 px, centrat, un rând, cuvintele schimbate pe bătăi.
- **Obiecte 3D** (generate cu Codex, fundal transparent): contorul, norul de furtună, panoul solar, postul de transformare, casca echipei. Intră în jurul cuvintelor și apoi zboară în harta consolei, unde devin markerii A, B, C.
- **Produsul.** Consola "Panou" (temă deschisă, exact ca în produs), mare, decupată: butonul "Rulează agentul" apăsat la scară uriașă, pașii Perceive → Estimate → Decide → Act bifați pe bătăi, traseele, scorul 0,87 cu factorii, bilanțul postului, scara de soluții pentru tensiune, cardul "Nu sunt sigur" cu "Aprobă" apăsat.
- **Tranziții.** Obiectele 3D → markerii de pe hartă; butonul → pașii; pastila "Aprobat" → fundalul închis de final.
- **Final pe cerneală.** Cifra față de baseline (doar din `reports/`), apoi logoul cu soarele care răsare.
- **Muzica.** Nouă, 120 BPM (1 bătaie = 15 cadre, 1 măsură = 2 s, 15 măsuri = 30 s), energică, cu câte o lovitură pe fiecare cuvânt și pe fiecare apăsare.

## Comenzi folosite

```bash
ffprobe -show_entries stream=... -show_entries format=... trust.mp4
ffmpeg -i trust.mp4 -vn -af ebur128=peak=true -f null -
npx -y hyperframes@0.9.19 measure cuts trust.mp4 --json
npx -y hyperframes@0.9.19 measure events trust.mp4 --map --json
npx -y hyperframes@0.9.19 measure look trust.mp4 --json
npx -y hyperframes@0.9.19 beats trust.mp4 --json
ffmpeg -ss <t> -t 3 -i trust.mp4 -vf fps=8,scale=320:-1 ...   # foi de contact la 8 cadre pe secundă
```
