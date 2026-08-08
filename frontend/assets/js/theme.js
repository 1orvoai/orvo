// ORVO theme manager. Applies theme instantly on load (before paint) to avoid flash.
const ORVO_THEME = {
  KEY: "orvo_theme",

  get() {
    return localStorage.getItem(this.KEY) || "dark";
  },

  apply(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(this.KEY, theme);
    const icons = document.querySelectorAll("[data-theme-icon]");
    icons.forEach((el) => {
      el.textContent = theme === "dark" ? "🌙" : "☀️";
    });
  },

  toggle() {
    const next = this.get() === "dark" ? "light" : "dark";
    this.apply(next);
    // Persist to backend if logged in (best-effort, non-blocking)
    if (typeof ORVO_API !== "undefined" && ORVO_API.isAuthenticated()) {
      ORVO_API.put("/api/users/profile", { theme: next }).catch(() => {});
    }
    return next;
  },

  init() {
    this.apply(this.get());
  },
};

// Apply immediately (script is loaded in <head> synchronously to prevent flash)
ORVO_THEME.init();
