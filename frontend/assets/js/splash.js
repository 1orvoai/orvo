// ORVO splash screen — shown briefly on every page load per requirements.
document.addEventListener("DOMContentLoaded", () => {
  const splash = document.getElementById("orvo-splash");
  if (!splash) return;
  const MIN_DISPLAY_MS = 1100;
  const start = Date.now();

  function hideSplash() {
    const elapsed = Date.now() - start;
    const remaining = Math.max(MIN_DISPLAY_MS - elapsed, 0);
    setTimeout(() => {
      splash.classList.add("hide");
      setTimeout(() => splash.remove(), 700);
    }, remaining);
  }

  if (document.readyState === "complete") {
    hideSplash();
  } else {
    window.addEventListener("load", hideSplash);
    // Failsafe in case 'load' never fires cleanly
    setTimeout(hideSplash, 3000);
  }
});
