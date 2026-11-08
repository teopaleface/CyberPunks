# 16 Revizie după cerințe

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Revizuiește read-only dacă versiunea integrată îndeplinește cererea lui Teo și limitele primei versiuni.

## Fișiere proprii

Acest job este read-only și nu deține fișiere pentru editare.

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- docs/PLAN-AGENTIC.md
- docs/agentic-prompts/INTERFACES.md
- docs/operations/AGENTIC-ACCEPTANCE.md

## Cerințe

1. Folosește exact același punct fix ca reviewerul 15, primit de la 00. Compară produsul livrat cu cererea: agentul coordonează pași și produce decizii bazate pe modelele proprii, cu analiză completă și efecte confirmate.

2. Verifică toate criteriile de acceptanță din plan: toate cazurile, incertitudine și capacitate, pregătire versus confirmare, traseu aprobat, raport pe rol și istoric care nu inventează reparația. Un buton sau o schemă fără conexiune reală este funcție nelivrată.

3. Verifică textul promisiunilor și dovezilor. Trei roluri pe site nu devin trei roluri pe telefon. Un apel API nu devine apel fizic, o randare nu devine imagine livrată și un rezultat acceptat de Meta nu devine citit.

4. Nu edita și nu implementa. Semnalează exact lipsurile care împiedică prima versiune, separat de extensiile amânate intenționat. Nu cere funcții din afara planului doar pentru că ar fi utile.

## Verificare și predare

Predă în mesaj constatări concrete cu fișier/linie sau criteriu, reproducere și impact. Menționează limitele dovezilor. Nu porni teste care scriu pe runtime, alte review-uri, apeluri sau mesaje.
