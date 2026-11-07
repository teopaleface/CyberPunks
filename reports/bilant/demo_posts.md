# Posturile pentru prezentare (demo-vara)

SIMULARE pe date publice, gândită pentru datele PPC. Fiecare caz e verificat cu problema ascunsă de noi (adevărul din construcție). Comanda: `uv run python -m cyberpunks.a_bilant.demo_story`.

## 1. Contorul și bilanțul se confirmă

- **PT-1180**, lucrarea `A-20250708-PT-1180`: Postul PT-1180: ~148 lei pe lună pierduți peste normal. Cauza probabilă (91%): contor de client defect sau manipulat, probabil clientul PT-1180-C107 (zile cu consum zero după consum normal). Recomand: întâi citire la distanță și jurnalul de evenimente al contorului.
- Contorul suspect: `PT-1180-C107` (zile cu consum zero după consum normal), consum dispărut ~7.5 kWh/zi; lipsa peste normal la post: ~7.1 kWh/zi.
- Adevărul: contorul are problema `zero` (meter_fault) din ziua 345 a simulării. Recomandarea: remote_reading (întâi citirea la distanță).

## 2. Dezechilibrul de faze, intrare pentru scara de soluții (C)

- **PT-1269**, lucrarea `A-20250708-PT-1269`: Postul PT-1269: ~5019 lei pe lună pierduți peste normal. Cauza probabilă (99%): pierdere tehnică (cablu, faze dezechilibrate). Recomand: echipa de rețea (cabluri, îmbinări, faze).
- Bilanțul vede pierderea pe cabluri de 2.2 ori normalul și estimează că faza cea mai încărcată are ~68% din case.
- Adevărul: din ziua 312, casele sunt împărțite 76% / 15% / 9% pe faze (u = 1.29).
- Pentru C: `extra.phase_rebalance_input` e intrarea treptei `phase_rebalance` (mută câteva case pe altă fază, o oră de lucru). Aceeași mutare scade și pierderile, și tensiunea pe faza încărcată.

## 3. Contorul postului setat greșit

- **PT-1210**: Postul PT-1210: contorul postului arată de 2.04 ori suma clienților (100% contor de post setat greșit). Lipsa de ~969 kWh/zi e doar pe hârtie. Recomand: întâi citire la distanță și jurnalul de evenimente al contorului (raportul de transformare).
- Adevărul: raportul de transformare greșit din ziua 104. Toate cele 11 posturi marcate așa au chiar această problemă: True.

## 4. Clientul trecut la postul greșit

- **PT-1165** (lucrarea `A-20250708-PT-1165`): Postul PT-1165: ~282 lei pe lună pierduți peste normal. Cauza probabilă (99%): client trecut la postul greșit în bază. Recomand: corecție în bază, fără deplasare.
- Adevărul: clientul `PT-1041-C039` e legat fizic la PT-1041, dar din ziua 175 apare în bază la PT-1165. PT-1041 are lipsă, PT-1165 are surplus. Corecția se face în birou, fără deplasare.
- PT-1041 în lista zilei: contor_client (remote_reading).

## Lista zilei, pe scurt

- 98 lucrări de bilanț; 97 sunt pe posturi care chiar au cel puțin o problemă ascunsă.
- Acțiuni: remote_reading 51, inspect_on_site 17, human_review 12, grid_inspection 11, office_correction 7.
