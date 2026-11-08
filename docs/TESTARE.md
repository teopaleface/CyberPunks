# Cum testezi Daybreak (pentru echipă)

Scris de orchestrator pe 7 nov. 2026, la 17:45, după ce partea tehnică s-a terminat. Verificat: 287 de teste trec, iar cele 14 ecrane ale consolei se deschid fără erori (`make web-smoke`).

## 1. Pornire (o singură comandă)

Din rădăcina repo-ului, pe branch-ul `Teo` sau `main`:

```bash
uv sync          # o dată, instalează Python și bibliotecile
make demo        # rulează agentul pe 8 iulie 2025, apoi pornește API-ul (8710) și consola (3710)
```

Deschide http://localhost:3710. Oprești totul cu Ctrl-C.

- Dacă porturile 8710 sau 3710 sunt deja ocupate (de exemplu de alt fir), `make demo` îți spune. Oprește întâi serverele vechi.
- Fără modele, doar pe planul salvat în repo: `make demo-offline` (fără butonul "Rulează agentul" și fără aprobări).

## 2. Ce verifici, ecran cu ecran

| Ecran | Ce trebuie să vezi |
|---|---|
| `/` Planul de mâine | Cifrele zilei, harta cu lucrările (A albastru, B mov, C chihlimbar), traseele echipelor, coada "Nu sunt sigur" (25), alerta principală |
| Butonul "Rulează agentul" | Pașii Perceive, Estimate, Decide, Act, cu timpii reali; planul se reface |
| `/lucrari/<id>` | Graficul potrivit sursei, motivele în cuvinte simple, cazurile asemănătoare, regula și pragul care au decis, ID-ul predicției și versiunea modelului |
| `/coada` | Cazurile "Nu sunt sigur"; Aprobă, Respinge, Amână schimbă planul și apar în jurnal |
| `/posturi` și `/posturi/<id>` | Harta posturilor (22 roșii, 41 galbene, 237 verzi), bilanțul postului, scara de soluții pentru tensiune, ofertele de baterii |
| `/alerte` | Alertele și mesajele către prosumatori (marcate "demo, nu s-a trimis") |
| `/jurnal` | Fiecare decizie, a agentului sau a omului, cu predicția și regula |
| `/modele` | Fiecare model față de metoda simplă, pe testul separat |
| `/ordine/<echipă>` | Ordinul de lucru în PDF |
| `/demo` | Modul pentru filmare și prezentare (săgețile sau tastele 1-5 schimbă scena) |
| `/?scenariu=maine` | Planul pe mâine, cu prognoza reală: puține lucrări C, pentru că soarele de noiembrie e slab |

## 3. Cifrele de știut (din `reports/`, testul separat)

| Model | Ce face | Model | Metoda simplă |
|---|---|---|---|
| A, contoare | Contor defect sau manipulat | 0,61 precizie pe problemele subtile; 0,81 pe SGCC (etichete reale) | 0,02; 0,11 |
| B, furtună | Zone cu pene de curent în 24 h | PR-AUC 0,28 | 0,15 |
| C, tensiune | Tensiunea maximă de mâine la post | eroare 0,0054 pu (circa 1,2 V); 86% din depășiri găsite | eroare 0,0227 pu |
| Bilanț | Pierderea normală pe post | eroare 5,2 kWh/zi | 14,7 kWh/zi (formula fizică) |

Atenție: precizia@K de 1,00 a lui A pe Londra nu se spune la prezentare (o umplu defectele evidente). Explicația e în `reports/A/error_analysis.md`.

## 4. Unde citești ca să înțelegi

- Întrebările probabile ale juriului, cu răspunsuri: `docs/QA-JURIU.md`.
- Cum se refac toate cifrele de la zero (32 de minute): `docs/REPRODUCERE.md`.
- Fiecare model: `reports/<A|B|C|bilant>/model_card.md` și `error_analysis.md`.
- Cum decide agentul: `reports/planner/README.md` și `config/planner.yaml`.
- Tema PPC și grila: `memory/07-tema-ppc.md`.

## 5. Dacă găsești un bug

Scrie-l în conversația orchestratorului, cu ecranul și ce ai făcut. După 10:30 se repară doar bug-uri, fără funcții noi.
