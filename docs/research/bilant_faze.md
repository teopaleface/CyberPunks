# Pierderi tehnice din dezechilibrul fazelor (bilanț pe post)

Data: 2026-11-07. Date sintetice: rețelele sunt SimBench (sintetice), sarcinile sunt cele din SimBench, parametrii de secvență zero sunt IPOTEZĂ. Nimic de aici nu e măsurat pe rețele reale.

## 1. Ce e modelul lui C

- Modelul lui C (`src/cyberpunks/c_prosumatori/powerflow.py`) e **echilibrat**: o singură fază, secvența pozitivă. Metoda e Z-bus (punct fix) pe matricea de admitanțe pandapower, rezolvată vectorizat pe toate orele deodată (pas orar).
- Fiecare casă e un punct de consum cu putere trifazată egală pe cele 3 faze. Neutrul nu apare. Deci pierderile din dezechilibru (curenți diferiți pe faze plus curent în neutru) **lipsesc** din model.
- Rezultatul lui C = pierderile "de bază" (cazul echilibrat). Noi le înmulțim cu un factor > 1 care depinde de cum sunt repartizate casele pe faze.

## 2. A mers `runpp_3ph`?

**Da.** pandapower 3.5.6, rețelele SimBench `1-LV-rural1--0-no_sw`, `1-LV-semiurb4--0-no_sw`, `1-LV-urban6--0-no_sw`. Durează ~0,03 s pe calcul.

Ce a trebuit adăugat (toate sunt IPOTEZE, rețeaua SimBench nu le are):

- Linii: `r0 = 4·r1`, `x0 = 4·x1`, `c0 = c1` (IPOTEZĂ tipică pentru cablu 4 fire; echivalent cu neutru de rezistență ≈ rezistența unei faze, adică r0 = r1 + 3·r_neutru cu r_neutru = r1).
- Transformator: grupa `Dyn`, `vk0 = vk`, `vkr0 = vkr`, `mag0_percent = 100`, `mag0_rx = 0`, `si0_hv_partial = 0,9` (IPOTEZĂ).
- Rețeaua de MT (ext_grid): `s_sc = 250 MVA`, `rx = 0,1`, `x0/x = 1`, `r0/x0 = 0,1` (IPOTEZĂ).
- Sarcini: `asymmetric_load` (P și Q pe faze). Sarcinile SimBench sunt înlocuite cu cele asimetrice, aceleași puteri.
- Atenție: nu pune `init="flat"` (în testul meu a dat rezultate greșite fără eroare). Fără `init` merge. Peste ~130 % încărcare a transformatorului cu dezechilibru mare nu converge.

Verificare: cu sarcina împărțită egal pe 3 faze, `runpp_3ph` dă **aceleași** pierderi ca `runpp` (cel echilibrat):

| rețea | linii kW (3ph / runpp) | trafo kW (3ph / runpp) |
|---|---|---|
| rural1 | 0,266 / 0,266 | 1,150 / 1,150 |
| semiurb4 | 3,359 / 3,359 | 3,335 / 3,335 |
| urban6 | 4,085 / 4,085 | 5,692 / 5,692 |

Deci modelul lui C e exact cazul "echilibrat" din runpp_3ph, iar raportul de mai jos e coerent cu el. (Valorile sunt la încărcarea de bază SimBench, 27-66 % din trafo.)

## 3. Experimentul

Pentru 3 topologii (rural1: 13 sarcini, trafo 160 kVA; semiurb4: 41, 400 kVA; urban6: 111, 630 kVA), 4 niveluri de încărcare (25, 50, 75, 100 % din trafo, în cazul echilibrat), s-au comparat pierderile **dependente de sarcină** (linii + trafo, fără pierderile de fier ale trafo, care nu depind de sarcină):

- (a) echilibrat: fiecare casă împărțită egal pe 3 faze (acesta e și modelul lui C);
- (b1) "fracție": fiecare casă împărțită pe faze cu aceleași procente (34/33/33, 45/30/25, 60/25/15, 80/10/10). Curat, fără hazard;
- (b2) "monofazat": fiecare casă pe **o singură** fază, aleasă la întâmplare cu probabilitățile 33/33/33 ("even") sau celelalte 4 repartiții, 12 extrageri pe caz. Asta e cazul real.

Metrici de dezechilibru:

- `u = max faza / medie − 1` (pentru 60/25/15: u = 0,8);
- `D = Σ (m_p − 1)²`, cu `m_p = 3·pondere_p` (pentru 60/25/15: D = 1,005). D ține cont de forma repartiției, u nu.

### Tabel: raport pierderi dezechilibrat / echilibrat (b1, fracție, încărcare 50 %)

| repartiție | u | D | total rural1 | total semiurb4 | total urban6 | doar linii (medie 3 rețele) | doar trafo (medie) |
|---|---|---|---|---|---|---|---|
| 34/33/33 | 0,02 | 0,001 | 1,000 | 1,000 | 1,000 | 1,001 | 1,000 |
| 45/30/25 | 0,35 | 0,14 | 1,084 | 1,135 | 1,118 | 1,18 | 1,05 |
| 60/25/15 | 0,80 | 1,00 | 1,440 | 1,716 | 1,620 | 1,95 | 1,27 |
| 80/10/10 | 1,40 | 2,94 | 2,312 | 3,206 | 2,882 | 3,88 | 1,81 |

"Total" depinde de cât din pierderile dependente de sarcină sunt în linii (rural1: 29 %, semiurb4: 62 %, urban6: 51 %; aproape neschimbat cu încărcarea). Liniile cresc mult, trafo-ul mai puțin.
Dependența de încărcare e mică: la 80/10/10 totalul merge de la 2,6 (25 %) la 3,4 (100 %), din cauza căderii de tensiune mai mari.

### Tabel: casele pe o singură fază, repartizate egal la întâmplare (b2, "even", 50 %)

| rețea | nr. sarcini | raport linii (medie, dev. std.) | raport total (medie) |
|---|---|---|---|
| rural1 | 13 | 3,99 (0,90) | 1,93 |
| semiurb4 | 41 | 1,70 (0,39) | 1,47 |
| urban6 | 111 | 1,39 (0,17) | 1,22 |

Concluzie importantă: **chiar și când casele sunt "egal împărțite" la nivel de post, pierderile din linii sunt de 1,4 până la 4 ori mai mari** decât în modelul echilibrat. Motivul: dezechilibrul se vede pe fiecare tronson, nu doar la trafo, și fiecare tronson servește puține case. Cu cât sunt mai puține case, cu atât mai mare efectul (rural1 are doar 13).

## 4. Formula de folosit în simulator

**Origine: ajustare (cele mai mici pătrate) pe cele 768 de rulări `runpp_3ph` de mai sus, ghidată de formula analitică din secțiunea 5.** Nu e o lege generală.

Notații: `p = (p_A, p_B, p_C)` ponderile reale ale caselor pe faze (suma 1), `N` = numărul de case (puncte de consum) din post, `D = Σ (3·p_f − 1)²`, `S = Σ p_f·(1 − p_f)` (pentru repartiție egală S = 2/3).

```
Pierderi linii   = L_linii_C   · (1 + 1,09 · (D + 9·S / (0,18·N)))
Pierderi cupru   = L_cupru_C   · (1 + 0,31 · (D + 9·S / N))
Pierderi fier    = neschimbate
```

- `L_linii_C`, `L_cupru_C` sunt pierderile din modelul echilibrat al lui C (liniile, respectiv pierderile din înfășurările trafo, adică pierderile trafo fără cele de fier).
- Termenul `D` = dezechilibrul mediu (cât de inegal sunt împărțite casele pe faze, global).
- Termenul `9·S/(c·N)` = efectul că o casă monofazată încarcă o singură fază ("granulație"). Dispare când N crește. `c = 0,18` înseamnă că ~18 % din case contează "efectiv" pentru pierderile din linii (IPOTEZĂ de calibrare, e media celor 3 rețele; ieșit din ajustare, nu din teorie). Dacă casele sunt împărțite exact egal pe faze (fiecare casă trifazată), pune S = 0 și D = 0.
- Pentru repartiție egală (S = 2/3): linii ≈ `1 + 1,09·(6/(0,18·N)) = 1 + 36/N`; trafo ≈ `1 + 1,9/N`.

Formula simplă dacă nu avem N și forma repartiției (doar pentru cazul "fracție", fără granulație): `raport_total ≈ 1 + k·u²` cu **k = 1,00**, R² = 0,88 (RMSE 0,29; eroare relativă maximă 32 %). Mai slabă decât formula cu D, pentru că u nu ține cont de forma repartiției (D: R² = 0,95 pe cazul fracție, vezi mai jos). Pe componente: linii `k = 1,59` (R² 0,96), trafo `k = 0,46` (R² 0,94).

Calitatea formulei cu D, N, S (modelul complet):

| set | R² | eroare relativă medie |
|---|---|---|
| total, caz fracție (b1, 48 de rulări) | 0,95 | 3,9 % |
| total, medii pe caz (108 combinații) | 0,94 | 5,1 % |
| total, casele monofazate, rulare cu rulare (b2) | 0,70 | 15 % |
| total, casele monofazate, medii pe caz | 0,93 | 6,1 % |

Pe rulări individuale monofazate R² e mic pentru că rezultatul depinde de care casă pe ce fază cade (hazard), mai ales în posturi mici (abatere standard 0,9 pe un raport de 4 în rural1). Formula dă **valoarea așteptată**, nu o rulare anume. Pentru total, ponderea liniilor `w` (0,29 / 0,62 / 0,51) vine din rețea: `raport_total = w·raport_linii + (1−w)·raport_cupru`. În simulator ea se obține direct din L_linii_C și L_cupru_C ale lui C, deci nu trebuie ținută separat.

Avertismente:

- Calibrat pe 3 rețele SimBench (13, 41, 111 sarcini) cu o sarcină SimBench = o "casă". Coeficienții 1,09 și 0,18 sunt IPOTEZĂ în afara acestui interval.
- Depinde de IPOTEZA neutrului (r0 = 4·r1). Cu neutru mai subțire (r_neutru = 2·r_faza) pierderile din linii cresc.
- Dezechilibrul acționează ca factor pe pierderile fiecărei ore; la ore cu sarcină mică efectul absolut e mic.

## 5. Derivare analitică (verificare independentă)

Pentru un tronson radial cu curenți pe faze `I_a, I_b, I_c` (fazori la 120°) și neutru `I_n`, rezistența neutrului `R_n`:

```
|I_n|² = I_a² + I_b² + I_c² − I_a·I_b − I_b·I_c − I_c·I_a
Pierderi = R · (I_a² + I_b² + I_c²) + R_n · |I_n|²
Echilibrat (aceeași putere totală): 3 · R · I_med²
```

Cu `m_f = I_f / I_med` (media 1, suma 3), `d_f = m_f − 1`, și `R_n = R`:

```
raport = 1 + (1 + 1,5)/3 · Σ d_f²  =  1 + 0,833 · D
```

Ex. 60/25/15: `1 + 0,833·1,005 = 1,84`; modelul complet dă 1,91 (linii). 80/10/10: analitic 3,45, numeric 3,71-4,03. Numeric e cu 5-15 % mai sus, din cauza căderii de tensiune (consum la putere constantă ⇒ curent mai mare pe faza încărcată). Deci coeficientul 1,09 din formula ajustată ≈ 0,833 · 1,3, adică are o parte teoretică (0,833) și o parte de efecte de rețea.

**Casa monofazată.** O casă de putere P pe o fază dă curent `P/V_faza`, triplu față de curentul pe fază al unei case trifazate cu aceeași putere (P/(3·V_faza)). Dacă n case egale se repartizează la întâmplare cu probabilități p_f, varianța ponderilor (valoare așteptată):

```
E[D_granulație] = 9 · Σ p_f (1 − p_f) / n     (repartiție egală: 6/n)
```

Pentru o casă singură (n = 1) factorul e 1 + 0,833·6 = **6**. Pentru n mare factorul tinde la 1. Factorul de corecție pentru "repartizare egală la întâmplare" pe un tronson cu n case: **1 + 5/n** (linii, teorie); la nivel de post, cu n_efectiv = 0,18·N (valoarea ajustată) devine **1 + 36/N** ⇒ rural1 (N=13) 3,8 (numeric 4,0), semiurb4 (N=41) 1,9 (numeric 1,7), urban6 (N=111) 1,3 (numeric 1,4).

**Validare numerică, un model analitic mic pe tronsoane** (script `/tmp/bilant_phase/analytic.py`): curentul pe fiecare tronson = suma sarcinilor din aval, pe faze, la tensiune 1 pu, fără cădere de tensiune; pierderi = `Σ R·(ΣI² + |I_n|²)`. Față de `runpp_3ph`:

- cazuri fracție: eroare 1-7 % la 34/33/33 - 60/25/15, până la 14 % la 80/10/10 (analiticul e sub numeric);
- 40 de repartiții monofazate aleatoare per rețea: corelație 0,998-1,000, raport mediu analitic/numeric 0,95-0,99.

Deci modelul pe tronsoane (rapid, fără pandapower) reproduce bine `runpp_3ph` și poate înlocui formula simplă dacă avem topologia.

## 6. Se văd pierderile în bilanț?

**Da.** Contorul de balanță al postului (la trafo, partea de JT) măsoară energia totală intrată; contoarele clienților măsoară ce a ieșit la ei. Pierderile = bilanț − suma clienților. Dezechilibrul crește curenții pe tronsoane și în neutru, deci crește I²R, deci diferența bilanț − Σ clienți crește. Din tabel: la 60/25/15 pierderile dependente de sarcină sunt de 1,4-1,7 ori cele din modelul echilibrat. Observații:

- Contoarele clienților (kWh) nu se schimbă (aceeași energie consumată), deci **tot excesul apare în bilanț ca "pierdere tehnică"**, fără să fie furt sau eroare de contor. În simulator trebuie separat: pierderi tehnice (modelul lui C × factorul de mai sus) vs. pierderi comerciale (furt, contoare defecte).
- Dezechilibrul scade și tensiunea la fazele încărcate (în rural1, la 80/10/10 și 167 % din capacitatea trafo, tensiunea minimă scade de la 0,95 la 0,77 pu, în prima trecere `run_grid.py`; peste ~130 % unele cazuri nu converg). Efect secundar, nu e în formulă.

## 7. Comenzi folosite (toate din `/Users/teo/.t3/worktrees/CyberPunks/Teo-bilant`)

Scripturile sunt în `/tmp/bilant_phase/` (în afara repo-ului):

```
uv run python /tmp/bilant_phase/probe.py        # structura rețelei rural1
uv run python /tmp/bilant_phase/t2.py           # runpp_3ph merge, sarcini asimetrice egale
uv run python /tmp/bilant_phase/check_bal.py    # 3ph echilibrat = runpp (tabelul din secțiunea 2)
uv run python /tmp/bilant_phase/run_grid.py     # prima trecere (scale 0.5-3), a căzut la 3x peste capacitate; informativ
uv run python /tmp/bilant_phase/run_grid2.py    # 768 rulări -> grid2.json (4 niveluri de încărcare, fracție + monofazat)
uv run python /tmp/bilant_phase/fit.py          # k pentru 1+k·u² și 1+k·D, tabele
uv run python /tmp/bilant_phase/analytic.py     # model analitic pe tronsoane vs runpp_3ph
uv run python /tmp/bilant_phase/fit2.py         # ajustarea formulei cu D, N, S
uv run python /tmp/bilant_phase/fit3.py         # R² pe medii
```

Biblioteca comună: `/tmp/bilant_phase/lib3.py` (`prep(topologie)` adaugă parametrii de secvență zero; `losses_3ph(net, ponderi_fază, factor_sarcină)` rulează `runpp_3ph`). 4 nuclee CPU maxim (`OMP_NUM_THREADS=4`).

## 8. Ce rămâne de făcut

- Alegerea realistă a repartiției pe faze pentru România (ce procent de branșamente monofazate, cum sunt împărțite pe faze la instalare). Fără date reale, folosim repartiția egală la întâmplare (S = 2/3, D = 0) ca scenariu de bază și 60/25/15 ca scenariu "rău". IPOTEZĂ.
- Validare pe o rețea cu date reale de la Rețele Electrice, dacă PPC dă contoare pe fază.
