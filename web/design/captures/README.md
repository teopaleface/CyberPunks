# Capturi pentru slideuri

Consola Daybreak la 1920×1080, pe planul real servit de API (`PLAN-demo-vara-20250708-170128-31d6`, generat pe 7 noiembrie 2026, la 17:01), scenariul „Zi de vară cu furtuni” (8 iulie 2025). Datele sunt sintetice, iar antetul fiecărei capturi o spune („Date sintetice în … din …”).

| Fișier | Ce arată |
|---|---|
| `01-planul-de-maine.png` | Planul de mâine: cifrele zilei, harta cu traseele, coada „Nu sunt sigur”, alerta principală cu ce a decis agentul, linia de timp a echipelor |
| `02-nu-sunt-sigur.png` | Lucrările pe care agentul le trimite la om, cu motivul și butoanele Aprobă, Respinge, Amână |
| `03-harta-posturilor.png` | Posturile de transformare, verde, galben, roșu după lei pierduți pe lună (pragurile din `config/planner.yaml`) |
| `04-lucrare-tensiune-C.png` | O lucrare C: tensiunea oră cu oră (P10–P90) față de limita de 1,10 pu și decizia agentului cu scara de soluții |
| `05-lucrare-contor-A.png` | O lucrare A: consumul zilnic față de normal, factorii modelului, decizia cu regula și pragurile în cuvinte |
| `06-jurnalul-deciziilor.png` | Jurnalul: fiecare decizie legată de predicție, versiunea modelului, regulă și praguri |
| `07-modelele.png` | Modelele A, B, C față de baseline, cu cifrele din rapoarte |
| `08-demo-scena-1.png` … `08-demo-scena-5.png` | Modul de prezentare `/demo`, tema închisă, cele cinci scene (scena 4: echipa E-RS-1 ajunge la Oravița la 14:00, înaintea furtunii de la 15:00) |

Lipsește încă pagina unui post cu graficul bilanțului: seriile bilanțului nu sunt publicate în API și nici în instantaneu (cererea e în `status/Teo-ui.md`). Captura se face când apar.

Cum se refac: `make api` și `make web-demo` (sau `make web`), apoi capturi la 1920×1080 ale adreselor `/`, `/coada`, `/?harta=posturi`, `/lucrari/C-20250708-PT-1269`, `/lucrari/A-20250708-MTR-011050`, `/jurnal`, `/modele`, `/demo?scena=1` … `5`.
