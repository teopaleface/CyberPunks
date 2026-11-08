# 06 Datele rapoartelor pe rol

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Construiește datele strict autorizate și textul de bază pentru rapoartele dispecerului, tehnicianului și clientului.

## Fișiere proprii

- src/cyberpunks/agentic/report_data.py
- tests/agentic/test_report_data.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- src/cyberpunks/operations/service.py
- web/components/operations/role-data.ts
- web/lib/operations/types.ts

## Cerințe

1. Produce variantele ReportData din 01 din snapshoturi și rezultate verificate, după verificarea domeniului curent. Nu trimite context brut către template și nu folosi date din machete ca sursă.

2. Pentru dispecer include lista de recomandări și excepții, cu acoperirea completă. Pentru tehnician include numai traseul aprobat al echipei și dovezile necesare. Pentru client include doar cazul și punctele proprii, fără fotografii/note interne sau suspiciuni despre terți.

3. Separă data scenariului istoric de momentul generării. Păstrează starea propus/aprobat și versiunea. Orele sunt planificate; nu le transforma în GPS sau timp de sosire live. Păstrează incertitudinea în toate reprezentările.

4. Textul, vocea, HTML-ul și PNG-ul trebuie să poată folosi aceleași valori. Totalurile și valorile derivate vin din funcțiile verificate. O predicție indisponibilă nu redevine validă printr-un rezumat.

## Verificare și predare

Verifică trei roluri, datele unei alte organizații, plan neaprobat, stare veche, câmpuri private injectate, caz fără evaluare și concordanța identificatorilor/cifrelor cu sursa completă. Predă exemplele de contract pentru 07 și 11, fără date personale.
