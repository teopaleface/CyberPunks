# Posturile pentru prezentare (demo-vara)

SIMULARE pe date publice, gândită pentru datele PPC. Fiecare caz e verificat cu problema ascunsă de noi (adevărul din construcție). Comanda: `uv run python -m cyberpunks.a_bilant.demo_story`.

## 1. Contorul (A) și bilanțul se confirmă

- Lucrarea A `A-20250708-MTR-001653` (contorul MTR-001653, postul **PT-1034**): Contor probabil defect (72%): 23% din intervalele de 30 de minute sunt negative; 3 zile cu consum negativ. Recomand: verificare la fața locului. Lipsesc ~2,5 kWh pe zi față de normal.
- Bilanțul postului PT-1034: lipsa a crescut cu ~19.0 kWh/zi în ultima săptămână; consumul contorului a scăzut cu ~28.2 kWh/zi.
- Scorul A 0.72 devine 0.98 după fuziune (`fuse`, regula R-FUSION-BILANT). Adevărul lui A: problema `negative`.

## 2. Dezechilibrul de faze, intrare pentru scara de soluții (C)

- **PT-1269**, lucrarea `A-20250708-PT-1269`: Postul PT-1269: ~5402 lei pe lună pierduți peste normal. Cauza probabilă (97%): pierdere tehnică (cablu, faze dezechilibrate). Recomand: echipa de rețea (cabluri, îmbinări, faze).
- Bilanțul vede pierderea pe cabluri de 2.4 ori normalul și estimează că faza cea mai încărcată are ~71% din case.
- Adevărul: din ziua 312, casele sunt împărțite 76% / 15% / 9% pe faze (u = 1.29).
- Pentru C: `extra.phase_rebalance_input` e intrarea treptei `phase_rebalance` (mută câteva case pe altă fază, o oră de lucru). Aceeași mutare scade și pierderile, și tensiunea pe faza încărcată.

## 3. Contorul postului setat greșit

- **PT-1210**: Postul PT-1210: contorul de balanță arată de 2.04 ori suma clienților (peste 99% contor de balanță defect sau setat greșit). Lipsa de ~938 kWh/zi e doar pe hârtie. Recomand: întâi citire la distanță și jurnalul de evenimente al contorului (raportul de transformare).
- Adevărul: raportul de transformare greșit din ziua 104. Toate cele 14 posturi marcate așa au chiar această problemă: False.

## 4. Clientul trecut la postul greșit

- **PT-1228** (lucrarea `A-20250708-PT-1228`): Postul PT-1228: lipsă de ~6.0 kWh/zi (~126 lei pe lună contați la postul greșit). Cauza probabilă (82%): client trecut la postul greșit în bază; tensiunea contorului seamănă cu a altui post. Perechea probabilă: PT-1010. Recomand: corecție în bază, fără deplasare.
- Adevărul: clientul `PT-1010-C040` e legat fizic la PT-1010, dar din ziua 64 apare în bază la PT-1228. PT-1010 are lipsă, PT-1228 are surplus. Corecția se face în birou, fără deplasare.
- PT-1010 în lista zilei: fără lucrare (lipsa e sub pragul de incertitudine).

## Lista zilei, pe scurt

- 84 lucrări de bilanț; 84 sunt pe posturi care chiar au cel puțin o problemă ascunsă.
- Acțiuni: inspect_on_site 28, office_correction 19, remote_reading 17, grid_inspection 14, human_review 6.
