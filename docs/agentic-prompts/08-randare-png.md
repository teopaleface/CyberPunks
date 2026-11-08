# 08 Transformarea HTML în PNG

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Transformă șabloanele fixe în imagini PNG private și reproductibile, cu limite de resurse.

## Fișiere proprii

- src/cyberpunks/agentic/png_renderer.py
- tests/agentic/test_png_renderer.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- pyproject.toml
- web/package.json
- src/cyberpunks/operations/photos.py
- docs/PLAN-AGENTIC.md

## Cerințe

1. Implementează interfața rendererului din 01. Verifică ce browser/headless renderer există deja local. Predă lui 00 o singură recomandare de dependență dacă este nevoie; nu modifica manifestele, lockfiles sau instalările globale.

2. Acceptă doar raportul/template-ul autorizat, nu HTML ori căi arbitrare. Blochează rețeaua, scripturile și accesul la fișiere care nu aparțin randării; limitează timpul, dimensiunile, numărul paginilor și volumul total. Nu folosi sesiunea Helium autentificată pentru rasterizarea documentelor.

3. Persistă octeții exacți și metadatele înaintea livrării: hash, lățime, înălțime, ordinea paginii, raport și versiune. O reluare a trimiterii folosește aceeași imagine, fără rerandare implicită cu alt conținut.

4. Returnează eroare tipizată și păstrează textul accesibil dacă randarea eșuează. Nu genera imagini publice și nu șterge artefactele altor joburi sau dovezile deja atașate.

## Verificare și predare

Testează timeout, HTML care încearcă rețea/script/file URL, cote, pagini multiple, hash stabil al artefactului folosit și eroare fără pierderea textului. Verifică dimensiunile și inspectează imaginile exacte rezultate. Separă probele reale de renderer de dublurile simulate.
