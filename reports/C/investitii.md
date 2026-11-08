# Raportul de investiții: posturile de transformare de modernizat (SINTETIC)

Generat de `uv run python -m cyberpunks.c_prosumatori.reports_c investments`. Posturile, rețelele și prosumatorii sunt sintetici; vremea e reală (Open-Meteo, 2025).

## De ce contează

- Ilfov e primul județ din țară la prosumatori: 21.647, cu 303,81 MW (ANRE, august 2026); București are 8.307 (134,94 MW). Ambele sunt în zona Rețele Electrice. La nivel național: 385.791 de prosumatori, 4.281,86 MW, 151.040 cu stocare (ANRE, 31 aug. 2026).
- Planul de dezvoltare Rețele Electrice pomenește posturi noi construite pentru reclamațiile de tensiune. Raportul ăsta arată unde ajunge o soluție ieftină și unde e nevoie de investiție.

## Cum am calculat

- Modelul C pe toate zilele din 2025, pentru fiecare dintre cele 300 posturi: zilele așteptate cu depășire (suma probabilităților), kWh fotovoltaici pierduți prin oprirea invertoarelor, valoarea lor (0,40 lei/kWh) și reclamațiile probabile (70 lei, Ord. ANRE 46/2021, la posturile cu cel puțin 10 zile cu depășire).
- Pentru posturile cu cel puțin 5 zile cu depășire pe an: scara de soluții pe cea mai însorită zi de referință (2025-04-28), cu efectele simulate pe rețeaua postului. Investiție = post nou sau nicio combinație ieftină nu aduce P90 sub 1,10 pu.

## Pe scurt

- 50 posturi din 300 au cel puțin o zi așteptată cu depășire pe an; 41 au cel puțin 5.
- Valoarea pierdută pe an la posturile cu probleme: 45.492 lei (energie și reclamații).
- Din primele 30 posturi, 30 se rezolvă fără investiție în rețea (faze, priză, limită de export, baterii); 0 au nevoie de post nou sau de cablu mai gros.

## Posturile, ordonate după valoarea pierdută pe an (primele 30)

| # | Post | Zona | kVA | kW panouri | kW/kVA | Zile cu depășire pe an | kWh pierduți pe an | Lei pe an | Soluția (cea mai ieftină care ajunge) | Cost (lei) | Recuperare (ani) | Investiție |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PT-1269 | IF-AFUMATI | 250 | 315 | 1,26 | 245 | 13.700 | 5.788 | oferte de baterii + limita de export | 26.973 | 4,7 | nu |
| 2 | PT-1076 | IF-CORNETU | 250 | 215 | 0,86 | 228 | 10.835 | 4.551 | 3 case mutate pe altă fază + limita de export | 18.735 | 4,1 | nu |
| 3 | PT-1300 | IF-STEFANESTII-DE-JOS | 160 | 246 | 1,54 | 225 | 9.591 | 4.109 | 3 case mutate pe altă fază + oferte de baterii + limita de export | 21.157 | 5,1 | nu |
| 4 | PT-1131 | IF-CHITILA | 250 | 224 | 0,90 | 214 | 9.180 | 3.903 | oferte de baterii + limita de export | 19.555 | 5,0 | nu |
| 5 | PT-1147 | IF-TUNARI | 400 | 298 | 0,74 | 217 | 6.785 | 3.036 | oferte de baterii + limita de export | 27.171 | 8,9 | nu |
| 6 | PT-1075 | IF-CORNETU | 160 | 170 | 1,06 | 202 | 6.252 | 2.662 | oferte de baterii + limita de export | 13.510 | 5,1 | nu |
| 7 | PT-1072 | IF-VOLUNTARI | 400 | 293 | 0,73 | 200 | 5.723 | 2.583 | limita de export | 26.515 | 10,3 | nu |
| 8 | PT-1005 | B-S1 | 250 | 261 | 1,04 | 172 | 4.197 | 1.910 | limita de export | 22.887 | 12,0 | nu |
| 9 | PT-1087 | IF-OTOPENI | 250 | 154 | 0,62 | 151 | 3.738 | 1.649 | mesaje de grup + limita de export | 12.751 | 7,7 | nu |
| 10 | PT-1255 | B-S6 | 630 | 299 | 0,47 | 174 | 3.339 | 1.637 | limita de export | 28.241 | 17,3 | nu |
| 11 | PT-1263 | B-S4 | 250 | 246 | 0,98 | 160 | 3.213 | 1.509 | 3 case mutate pe altă fază + o treaptă de priză + oferte de baterii | 1.976 | 1,3 | nu |
| 12 | PT-1119 | IF-STEFANESTII-DE-JOS | 400 | 417 | 1,04 | 158 | 2.366 | 1.310 | 3 case mutate pe altă fază + o treaptă de priză + oferte de baterii | 1.968 | 1,5 | nu |
| 13 | PT-1082 | IF-1-DECEMBRIE | 250 | 129 | 0,52 | 165 | 2.605 | 1.154 | mesaje de grup + oferte de baterii + limita de export | 10.282 | 8,9 | nu |
| 14 | PT-1015 | IF-OTOPENI | 160 | 275 | 1,72 | 144 | 2.075 | 1.117 | 3 case mutate pe altă fază + o treaptă de priză + oferte de baterii | 1.974 | 1,8 | nu |
| 15 | PT-1047 | IF-MAGURELE | 250 | 313 | 1,25 | 127 | 1.702 | 1.024 | 3 case mutate pe altă fază + o treaptă de priză + oferte de baterii | 1.974 | 1,9 | nu |
| 16 | PT-1058 | IF-AFUMATI | 160 | 246 | 1,54 | 142 | 1.652 | 906 | limita de export | 19.630 | 21,7 | nu |
| 17 | PT-1252 | IF-POPESTI-LEORDENI | 160 | 272 | 1,70 | 143 | 1.396 | 859 | 3 case mutate pe altă fază + o treaptă de priză + oferte de baterii | 1.988 | 2,3 | nu |
| 18 | PT-1196 | IF-GLINA | 160 | 141 | 0,88 | 132 | 1.418 | 700 | limita de export | 13.242 | 18,9 | nu |
| 19 | PT-1062 | IF-JILAVA | 630 | 375 | 0,60 | 79 | 341 | 570 | 3 case mutate pe altă fază + o treaptă de priză | 2.184 | 3,8 | nu |
| 20 | PT-1296 | IF-CLINCENI | 160 | 254 | 1,59 | 74 | 540 | 475 | o treaptă de priză + mesaje de grup + oferte de baterii | 1.659 | 3,5 | nu |
| 21 | PT-1282 | B-S4 | 630 | 478 | 0,76 | 50 | 14 | 439 | o treaptă de priză | 1.698 | 3,9 | nu |
| 22 | PT-1297 | IF-BRAGADIRU | 250 | 161 | 0,64 | 90 | 563 | 372 | o treaptă de priză + oferte de baterii | 1.648 | 4,4 | nu |
| 23 | PT-1085 | B-S1 | 250 | 249 | 1,00 | 33 | 20 | 302 | o treaptă de priză + mesaje de grup | 1.641 | 5,4 | nu |
| 24 | PT-1246 | IF-MAGURELE | 400 | 311 | 0,78 | 28 | 22 | 282 | o treaptă de priză | 1.698 | 6,0 | nu |
| 25 | PT-1193 | IF-DOMNESTI | 400 | 221 | 0,55 | 10 | 20 | 260 | o treaptă de priză | 1.866 | 7,2 | nu |
| 26 | PT-1097 | B-S1 | 400 | 168 | 0,42 | 48 | 252 | 255 | o treaptă de priză + mesaje de grup | 1.869 | 7,3 | nu |
| 27 | PT-1168 | IF-MOGOSOAIA | 160 | 115 | 0,72 | 63 | 298 | 252 | 3 case mutate pe altă fază + o treaptă de priză | 1.956 | 7,8 | nu |
| 28 | PT-1214 | B-S1 | 250 | 234 | 0,94 | 32 | 15 | 223 | o treaptă de priză + mesaje de grup | 1.869 | 8,4 | nu |
| 29 | PT-1059 | IF-BUFTEA | 250 | 188 | 0,75 | 24 | 33 | 216 | o treaptă de priză | 1.866 | 8,6 | nu |
| 30 | PT-1137 | B-S4 | 160 | 197 | 1,23 | 17 | 9 | 193 | o treaptă de priză | 1.638 | 8,5 | nu |

Recuperarea = costul soluției / valoarea pierdută pe an. Toate costurile vin din `config/economics.yaml` (IPOTEZĂ unde nu au sursă).
