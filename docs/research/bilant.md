# Bilanț pe post: cercetarea din faza 0

7 nov. 2026. Detaliile și toate sursele sunt în două note:
- `bilant_lit.md`: CPT-ul Rețele Electrice, bilanțul pe post la distribuitori, literatura despre pierderile comerciale (NTL), clientul legat la postul sau la faza greșită, efectul fazelor dezechilibrate;
- `bilant_faze.md`: cum adăugăm fazele în calculul de rețea al lui C, care e echilibrat. Formula vine din 768 de rulări `pandapower.runpp_3ph`.

## Ce reținem

1. **Problema e reală și are cifre.** CPT Muntenia: 10,78% în 2018 și 8,66% în 2023, față de 8,97% recunoscut de ANRE; 63,54% din CPT e pe joasă tensiune (Plan RER 2024-2033, prin `memory/12-probleme-reale-ppc-2026.md`). Planul de dezvoltare RER 2026-2035 dă, pentru 2024, 9,05% în Muntenia, 9,11% în Banat și 7,98% în Dobrogea. Pe JT se produc 65% din pierderi în Muntenia și Banat. Ținta JT în Muntenia scade de la 10,90% (2025) la 9,92% (2029). Ord. ANRE 67/2024 cere o scădere de cel puțin 15% a țintei CPT pe JT în perioada a V-a de reglementare.
2. **Contoarele de bilanț sunt în planul RER.** Planul cere ca infrastructura de contorizare inteligentă să permită cel puțin un contor de bilanț în fiecare post, ca funcție obligatorie. Pilotul din Alba Iulia: 8 posturi, 1.342 de clienți, 8 contoare de bilanț. Întrebarea pentru mentorul PPC rămâne: câte posturi au azi contor de bilanț și cât de bună e lista client → post?
3. **Furtul depistat e mic față de pierderi.** În 2024: 1.394 MWh în Muntenia, sub 0,2% din CPT. În 2025: circa 3.900 de intervenții neautorizate și circa 10 GWh estimați sustrași (Digi24, prin `memory/12`). Bilanțul arată unde se pierde energia fără să ghicească pe fiecare contor.
4. **Pierderea tehnică normală pe JT.** Reperul simulării: 3-6% din energia care trece prin post (IPOTEZĂ; 5,8-6,6% pe toată distribuția în UK, 4-6% pentru transformatoare plus cabluri în fișa UE). Pierderea crește cu pătratul încărcării (factorul de pierderi 0,3·LF + 0,7·LF²). Simularea noastră dă o mediană de 3,8% pe cele 300 de posturi ale hărții, din `reports/bilant/metrics.json`.
5. **Fazele.** Calculul lui C e exact cazul echilibrat (`runpp_3ph` cu sarcina împărțită egal dă aceleași pierderi). Casele monofazate și fazele inegale cresc pierderile pe linii: factorul e `1 + 1,09·(D + 9S/(0,18·N))` (D = Σ(3p−1)², S = Σp(1−p), N = numărul de case; R² = 0,95 pe cazurile împărțite pe procente). O fază cu 60% din case aproape dublează pierderile pe linii.
6. **Clientul la postul greșit.** Corelația variațiilor de tensiune ale contorului cu ale postului găsește postul corect în 95-100% din cazuri în comparația din 2022 și în 83% din cazuri în teren (National Grid). Singura rată publică de erori de mapare în GIS: circa 5% (ComEd). Noi folosim tensiunea măsurată în contor (o dă calculul de rețea) și potrivirea lipsei de la un post cu surplusul de la vecin.
7. **Ce nu am găsit:** câștigul publicat de precizie când se combină bilanțul cu scorul pe contor. De aceea cifra „cu bilanț față de fără” o măsurăm noi, pe simulare, și o prezentăm ca atare.

## Decizii pentru implementare

- Lumea: posturile din registrul C (aceeași rețea, din seed), calculul de rețea al lui C, pierderile pe fiecare cablu din curenți (|I|²R), corecția de faze de mai sus, plus 30% pentru variația din interiorul orei și o calibrare ×2,5 ± 35% între posturi pentru ce nu are SimBench (branșamente, îmbinări vechi). Toate sunt marcate IPOTEZĂ.
- Contoarele: eroare fixă mică (clasa 1 la clienți, 0,5S la post), consum propriu de 1,5 W nemăsurat, goluri de comunicație la 3% din contoare. Prosumatorii au contoare bidirecționale, iar bilanțul folosește energia netă (consum minus injecție).
- Problemele: tabelul din `src/cyberpunks/a_bilant/problems.py`, cu formulele de contor ale firului A.
