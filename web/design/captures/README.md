# Capturi pentru slideuri

Consola Daybreak după trecerea de simplificare (Varianta 1, aleasă de Teo), la 1920×1080, pe planul real servit de API (`PLAN-demo-vara-20250708-182006-043b`, generat pe 7 noiembrie 2026, la 18:20), scenariul „Zi de vară cu furtuni” (8 iulie 2025). Datele sunt sintetice, iar antetul fiecărei capturi o spune.

| Fișier | Ce arată |
|---|---|
| `01-planul-de-maine.png` | Primul ecran: fraza zilei, o singură acțiune, trei cifre, următorul caz de decis, echipele pe scurt, harta mică doar cu traseele |
| `02-echipele-de-maine.png` | Fereastra „Echipele de mâine”: lista echipelor, cu plecarea și întoarcerea |
| `03-detaliile-zilei.png` | Panoul „Detaliile zilei”: toate cifrele planului și alertele, la cerere |
| `04-de-decis.png` | Cazurile pe care agentul nu le poate decide singur: o frază, trei butoane, detaliile tehnice închise |
| `05-postul-PT-1269.png` | Pagina unui post: verdictul într-o frază, apoi graficul bilanțului (ieșit din post față de suma clienților) |
| `06-lucrare-tensiune-C.png` | O lucrare C: verdictul, combinația aleasă, tensiunea oră cu oră |
| `07-lucrare-contor-A.png` | O lucrare A: verdictul, consumul zilnic față de normal |
| `08-harta-mare.png` | Harta mare cu linia de timp a echipelor (`/harta`), pentru cine vrea toate detaliile |
| `09-jurnalul-deciziilor.png` | Jurnalul: fiecare decizie legată de predicție, model, regulă și praguri |
| `10-modelele.png` | Modelele A, B, C față de baseline |
| `11-demo-scena-1.png` … `11-demo-scena-5.png` | Prezentarea `/demo`, tema închisă, cele cinci scene, cu subtitrarea pe banda ei |

Graficul bilanțului din `05` folosește seriile firului de bilanț din `outputs/series/demo-vara/` (ieșirea modelului, în afara git); în API și în instantaneu nu sunt încă publicate (cererea e în `status/Teo-ui.md`).

Cum se refac: `make api` și `make web-demo` (sau `make web`), apoi capturi la 1920×1080 ale adreselor `/` (plus fereastra „Vezi echipele” și panoul „Detaliile zilei”), `/coada`, `/posturi/PT-1269`, `/lucrari/C-20250708-PT-1269`, `/lucrari/A-20250708-MTR-011050`, `/harta`, `/jurnal`, `/modele`, `/demo?scena=1` … `5`.
