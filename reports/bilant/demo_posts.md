# Posturile pentru prezentare (demo-vara)

SIMULARE pe date publice, gândită pentru datele PPC. Fiecare caz e verificat cu problema ascunsă de noi (adevărul din construcție). Comanda: `uv run python -m cyberpunks.a_bilant.demo_story`.

## 1. Contorul (A) și bilanțul se confirmă

- Lucrarea A `A-20250708-MTR-011937` (contorul MTR-011937, postul **PT-1224**): Contor probabil defect (94%): consum zero în ultimele 5 zile; doar 86% valori diferite în ultimele 4 săptămâni. Recomand: verificare la fața locului. Lipsesc ~0,3 kWh pe zi față de normal.
- Bilanțul postului PT-1224: lipsa a crescut cu ~43.7 kWh/zi în ultima săptămână; consumul contorului a scăzut cu ~40.2 kWh/zi.
- Scorul A 0.71 devine 0.96 după fuziune (`fuse`, regula R-FUSION-BILANT). Adevărul lui A: problema `zero`.
- Bilanțul are și lucrarea lui pe post: Postul PT-1224: ~148 lei pe lună pierduți peste normal. Nu sunt sigur de cauză (cauza cea mai probabilă are sub 50%): contor de client defect sau manipulat 29% sau pierdere tehnică (cablu, faze dezechilibrate) 26%. Decide un om.

## 2. Dezechilibrul de faze, intrare pentru scara de soluții (C)

- **PT-1269**, lucrarea `A-20250708-PT-1269`: Postul PT-1269: ~5146 lei pe lună pierduți peste normal. Cauza probabilă (99%): pierdere tehnică (cablu, faze dezechilibrate). Recomand: echipa de rețea (cabluri, îmbinări, faze).
- Bilanțul vede pierderea pe cabluri de 2.2 ori normalul și estimează că faza cea mai încărcată are ~69% din case.
- Adevărul: din ziua 312, casele sunt împărțite 76% / 15% / 9% pe faze (u = 1.29).
- Pentru C: `extra.phase_rebalance_input` e intrarea treptei `phase_rebalance` (mută câteva case pe altă fază, o oră de lucru). Aceeași mutare scade și pierderile, și tensiunea pe faza încărcată.

## 3. Contorul postului setat greșit

- **PT-1210**: Postul PT-1210: contorul postului arată de 2.04 ori suma clienților (100% contor de post setat greșit). Lipsa de ~937 kWh/zi e doar pe hârtie. Recomand: întâi citire la distanță și jurnalul de evenimente al contorului (raportul de transformare).
- Adevărul: raportul de transformare greșit din ziua 104. Toate cele 14 posturi marcate așa au chiar această problemă: False.

## 4. Clientul trecut la postul greșit

- **PT-1155** (lucrarea `A-20250708-PT-1155`): Postul PT-1155: lipsă de ~67.4 kWh/zi (~1416 lei pe lună contați la postul greșit). Cauza probabilă (99%): client trecut la postul greșit în bază; tensiunea contorului seamănă cu a altui post. Perechea probabilă: PT-1029. Recomand: corecție în bază, fără deplasare.
- Adevărul: clientul `PT-1029-C096` e legat fizic la PT-1029, dar din ziua 302 apare în bază la PT-1155. PT-1029 are lipsă, PT-1155 are surplus. Corecția se face în birou, fără deplasare.
- PT-1029 în lista zilei: client_post_gresit (office_correction).

## Lista zilei, pe scurt

- 76 lucrări de bilanț; 76 sunt pe posturi care chiar au cel puțin o problemă ascunsă.
- Acțiuni: inspect_on_site 27, remote_reading 21, office_correction 13, grid_inspection 10, human_review 5.
