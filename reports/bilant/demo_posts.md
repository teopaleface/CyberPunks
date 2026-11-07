# Posturile pentru prezentare (demo-vara)

SIMULARE pe date publice, gândită pentru datele PPC. Fiecare caz e verificat cu problema ascunsă de noi (adevărul din construcție). Comanda: `uv run python -m cyberpunks.a_bilant.demo_story`.

## 1. Contorul (A) și bilanțul se confirmă

- Lucrarea A `A-20250708-MTR-007521` (contorul MTR-007521, postul **PT-1145**): Contor probabil defect (69%): consum zero în ultimele 5 zile; doar 86% valori diferite în ultimele 4 săptămâni. Recomand: verificare la fața locului. Lipsesc ~2,2 kWh pe zi față de normal.
- Bilanțul postului PT-1145: lipsa a crescut cu ~7.1 kWh/zi în ultima săptămână; consumul contorului a scăzut cu ~7.3 kWh/zi.
- Scorul A 0.69 devine 0.83 după fuziune (`fuse`, regula R-FUSION-BILANT). Adevărul lui A: problema `zero`.
- Bilanțul are și lucrarea lui pe post: Postul PT-1145: contorul postului arată de 2.03 ori suma clienților (100% contor de post setat greșit). Lipsa de ~582 kWh/zi e doar pe hârtie. Recomand: întâi citire la distanță și jurnalul de evenimente al contorului (raportul de transformare).

## 2. Dezechilibrul de faze, intrare pentru scara de soluții (C)

- **PT-1269**, lucrarea `A-20250708-PT-1269`: Postul PT-1269: ~5146 lei pe lună pierduți peste normal. Cauza probabilă (99%): pierdere tehnică (cablu, faze dezechilibrate). Recomand: echipa de rețea (cabluri, îmbinări, faze).
- Bilanțul vede pierderea pe cabluri de 2.2 ori normalul și estimează că faza cea mai încărcată are ~69% din case.
- Adevărul: din ziua 312, casele sunt împărțite 76% / 15% / 9% pe faze (u = 1.29).
- Pentru C: `extra.phase_rebalance_input` e intrarea treptei `phase_rebalance` (mută câteva case pe altă fază, o oră de lucru). Aceeași mutare scade și pierderile, și tensiunea pe faza încărcată.

## 3. Contorul postului setat greșit

- **PT-1210**: Postul PT-1210: contorul postului arată de 2.04 ori suma clienților (100% contor de post setat greșit). Lipsa de ~937 kWh/zi e doar pe hârtie. Recomand: întâi citire la distanță și jurnalul de evenimente al contorului (raportul de transformare).
- Adevărul: raportul de transformare greșit din ziua 104. Toate cele 12 posturi marcate așa au chiar această problemă: True.

## 4. Clientul trecut la postul greșit

- **PT-1165** (lucrarea `A-20250708-PT-1165`): Postul PT-1165: ~1676 lei pe lună pierduți peste normal. Cauza probabilă (99%): client trecut la postul greșit în bază. Recomand: corecție în bază, fără deplasare.
- Adevărul: clientul `PT-1041-C039` e legat fizic la PT-1041, dar din ziua 175 apare în bază la PT-1165. PT-1041 are lipsă, PT-1165 are surplus. Corecția se face în birou, fără deplasare.
- PT-1041 în lista zilei: fără lucrare (lipsa e sub pragul de incertitudine).

## Lista zilei, pe scurt

- 89 lucrări de bilanț; 89 sunt pe posturi care chiar au cel puțin o problemă ascunsă.
- Acțiuni: inspect_on_site 26, remote_reading 22, grid_inspection 16, office_correction 14, human_review 11.
