# Audit și aliniere vizuală a consolei

7 noiembrie 2026, 22:04, București.

Teo a cerut concentrarea pe design și un audit al landingului și consolei. Landingul îi place. Consola i se pare greu de citit și de înțeles, cu alte fonturi și culori. A autorizat mai mulți subagenți pentru rezolvare.

Reperul este landingul integrat din `web/site`, servit la `/`, nu aplicația veche separată din `landing/`. Consola este la `/app`.

Modificări locale: negru, alb și galben pentru acțiuni; Geist pentru text și carduri, Unbounded pentru titluri; trei cifre principale, planul și cazul de decis separate, restul la cerere. Navigare grupată, „De verificat” în loc de „Nu sunt sigur”, meniu complet pe telefon. Pe telefon, următorul caz de decis apare înaintea cifrelor.

Auditul și limitele verificării sunt în `web/design/AUDIT-UI-UX.md`. Nu s-a făcut deploy. Conflictul anterior din `memory/journal.md` a fost integrat de alt fir în timpul lucrului, în commitul a1862c1. Acest task nu a modificat conturile/API.

## Revizuire de utilitate și limba produsului

Teo a respins eticheta „Consola dispecerului” și căutarea globală din antet și a cerut un audit UI/UX mai strict. Produsul, atât landingul cât și consola, trebuie să fie în engleză. Comentariile și conversația cu Teo pot rămâne în română. Antetul desktop se elimină; navigarea operațională rămâne în sidebar, iar instrumentele agentului se deschid la cerere. Nu adăugăm texte sau controale doar ca să umple spațiul.
