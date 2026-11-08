// Shared by the static landing. The console uses next-themes with the same key.
(() => {
  let theme = "dark";
  try {
    if (localStorage.getItem("daybreak-theme") === "light") theme = "light";
  } catch {}
  const root = document.documentElement;
  root.classList.remove("light", "dark");
  root.classList.add(theme);
  root.dataset.theme = theme;
  root.style.colorScheme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", theme === "light" ? "#ffffff" : "#000000");
})();
