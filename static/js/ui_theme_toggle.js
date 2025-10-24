/* ============================================
   Mina UI Theme Toggle
   ============================================ */

(() => {
  const STORAGE_KEY = "mina-theme";
  const root = document.documentElement;
  const toggleBtn = document.querySelector("[data-theme-toggle]");

  // 1. Load saved or system preference
  const saved = localStorage.getItem(STORAGE_KEY);
  const systemPref = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  const activeTheme = saved || systemPref;
  root.setAttribute("data-theme", activeTheme);

  // 2. Listen for manual toggle
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const current = root.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      localStorage.setItem(STORAGE_KEY, next);
      toggleBtn.setAttribute("aria-pressed", next === "dark");
    });
  }

  // 3. React to system changes
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", e => {
    const theme = e.matches ? "dark" : "light";
    root.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
  });
})();