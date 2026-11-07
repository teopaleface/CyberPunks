# Captura consolei pentru film (provizorie)

`panou_film.html` și `data_film.js` sunt copia machetei "Panou" a firului UI (`web/design/directions/` pe branch-ul `Teo-ui`), cu data zilei de demo (marți, 8 iulie 2025) și cazul de furtună mutat în Banat (Reșița), ca filmul să fie coerent cu scenariul `demo-vara`. Datele sunt SINTETICE (exemple de test), etichetate așa și în consolă.

Captura la rezoluție dublă (3840×2160), cu harta OpenFreeMap reală:

```bash
export AGENT_BROWSER_SESSION=prez-panou
agent-browser set viewport 1920 1080 2
agent-browser open file://$PWD/presentation/scripts/consola/panou_film.html
agent-browser wait --fn "window.__ready === true"
agent-browser screenshot presentation/video/assets/ui/consola_8iulie@2x.png
agent-browser close
```

Se înlocuiește cu captura consolei reale (modul `/demo`, după ora 01:00).
