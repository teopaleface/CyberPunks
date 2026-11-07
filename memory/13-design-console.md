# Audit și aliniere vizuală a consolei

7 noiembrie 2026, 22:04, București.

Teo a cerut concentrarea pe design și un audit al landingului și consolei. Landingul îi place. Consola i se pare greu de citit și de înțeles, cu alte fonturi și culori. A autorizat mai mulți subagenți pentru rezolvare.

Reperul este landingul integrat din `web/site`, servit la `/`, nu aplicația veche separată din `landing/`. Consola este la `/app`.

Modificări locale: negru, alb și galben pentru acțiuni; Geist pentru text și carduri, Unbounded pentru titluri; trei cifre principale, planul și cazul de decis separate, restul la cerere. Navigare grupată, „De verificat” în loc de „Nu sunt sigur”, meniu complet pe telefon. Pe telefon, următorul caz de decis apare înaintea cifrelor.

Auditul și limitele verificării sunt în `web/design/AUDIT-UI-UX.md`. Nu s-a făcut deploy. Conflictul anterior din `memory/journal.md` a fost integrat de alt fir în timpul lucrului, în commitul a1862c1. Acest task nu a modificat conturile/API.

## Revizuire de utilitate și limba produsului

Teo a respins eticheta „Consola dispecerului” și căutarea globală din antet și a cerut un audit UI/UX mai strict. Produsul, atât landingul cât și consola, trebuie să fie în engleză. Comentariile și conversația cu Teo pot rămâne în română. Antetul desktop se elimină; navigarea operațională rămâne în sidebar, iar instrumentele agentului se deschid la cerere. Nu adăugăm texte sau controale doar ca să umple spațiul.

## Light și Dark

7 noiembrie, 23:04. Teo a cerut ca ordinul alb să fie întunecat și să existe un toggle Light/Dark. Ambele aplicații folosesc alegerea locală `daybreak-theme`, cu Dark implicit. Consola are comutator în meniul lateral și în meniul mobil; landingul lângă cont. Ordinul urmează tema pe ecran, dar se tipărește alb. Harta recreează împreună stilul și markerii la schimbare.

QA într-o copie separată din cauza modificărilor simultane de autentificare: date din API-ul local existent, fără secrete sau setări de automatizare. Comutarea, persistența între landing/consolă, meniul mobil și culorile print sunt verificate în browser. Harta păstrează 28 de markeri după Dark → Light → Dark. Fără deploy sau acțiuni de aprobare/rulare.

## Preluare selectivă din design

8 noiembrie, 00:16. La cererea lui Teo, `origin/design` a fost actualizat și comparat cu Teo. Ultimul commit disponibil este `427afd8`, 8 noiembrie 00:08. Modificările de reguli sunt o schemă de prezentare a deciziilor; `config/`, codul agentului și testele nu au modificări față de baza comună. Nu se face merge complet: branchul ușor șterge intenționat modele și date și păstrează texte/autentificare vechi.

Preluat în landing: prima pagină mai scurtă, un număr principal animat, fluxul deciziilor cu accent pe verificarea umană, cronologia echipelor și ancorarea razei între butoane. Adaptat la engleză, Light/Dark și mișcare redusă. Valoarea rămâne estimată, nu economii realizate; intervalele de lucru sunt marcate ca estimate. Rapoartele, cerințele de date și limitele rămân în paginile de detalii. Fără schimbări în logică, date sau autentificare; fără publicare.
