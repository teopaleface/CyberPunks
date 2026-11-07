# CyberPunks: Tura de mâine

Proiectul echipei CyberPunks la SmartHack XI 2026 (7-8 noiembrie, București), pe tema PPC "24h to Power PPC": un agent AI care decide unde merg mâine echipele de teren Rețele Electrice, pe baza a trei modele ML antrenate de echipă (contoare defecte sau manipulate, risc de avarii la furtună, tensiune prea mare din cauza prosumatorilor), și explică fiecare decizie.

Stare: în lucru, vezi [`status/ACUM.md`](status/ACUM.md). Planul: [`docs/PLAN.md`](docs/PLAN.md). Formatele de date: [`docs/CONTRACTS.md`](docs/CONTRACTS.md). Contextul și research-ul: [`memory/`](memory/INDEX.md).

## Pornire rapidă

```bash
uv sync          # Python 3.12, toate dependențele
make check       # lint și teste
make validate-fixtures
```

Pașii completi de reproducere (date, antrenare, evaluare, demo) se adaugă pe măsură ce firele livrează.
