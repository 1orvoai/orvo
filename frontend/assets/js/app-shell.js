// ORVO app shell — injected into every authenticated page (#orvo-shell-sidebar / #orvo-shell-topbar).
const ORVO_NAV_ITEMS = [
  { href: "/dashboard.html", label: "Dashboard", icon: "📊" },
  { href: "/trading.html", label: "Trading", icon: "📈" },
  { href: "/settings.html", label: "Settings", icon: "⚙️" },
  { href: "/profile.html", label: "Profile", icon: "👤" },
];

async function orvoInitAppShell({ requireAdmin = false } = {}) {
  if (!ORVO_API.isAuthenticated()) {
    window.location.href = "/login.html";
    return null;
  }

  let user;
  try {
    user = await ORVO_API.get("/api/auth/me");
  } catch (e) {
    window.location.href = "/login.html";
    return null;
  }

  if (requireAdmin && user.role !== "admin") {
    orvoShowToast("Admin access required.", "error");
    window.location.href = "/dashboard.html";
    return null;
  }

  const currentPath = window.location.pathname;
  const sidebarEl = document.getElementById("orvo-shell-sidebar");
  if (sidebarEl) {
    let links = ORVO_NAV_ITEMS.map(
      (item) => `
      <a href="${item.href}" class="sidebar-link ${currentPath.includes(item.href) ? "active" : ""}">
        <span>${item.icon}</span><span>${item.label}</span>
      </a>`
    ).join("");
    if (user.role === "admin") {
      links += `
      <a href="/admin.html" class="sidebar-link ${currentPath.includes("/admin.html") ? "active" : ""}">
        <span>🛡️</span><span>Admin Panel</span>
      </a>`;
    }
    sidebarEl.innerHTML = `
      <div class="px-4 py-6">
        <a href="/index.html" class="text-2xl font-extrabold tracking-widest block mb-8" style="color:var(--accent)">ORVO</a>
        <nav class="space-y-1">${links}</nav>
      </div>
      <div class="px-4 py-4 mt-auto">
        <button id="orvo-logout-btn" class="sidebar-link w-full text-left">
          <span>🚪</span><span>Logout</span>
        </button>
      </div>
    `;
    document.getElementById("orvo-logout-btn").addEventListener("click", async () => {
      try { await ORVO_API.post("/api/auth/logout"); } catch (e) {}
      ORVO_API.clearToken();
      window.location.href = "/login.html";
    });
  }

  const topbarEl = document.getElementById("orvo-shell-topbar");
  if (topbarEl) {
    topbarEl.innerHTML = `
      <div class="flex items-center justify-between w-full">
        <div class="text-sm" style="color:var(--text-secondary)">Welcome back, <span style="color:var(--text-primary)" class="font-semibold">${user.full_name}</span></div>
        <div class="flex items-center gap-3">
          <button onclick="ORVO_THEME.toggle()" class="btn-secondary" data-theme-icon>🌙</button>
          <a href="/profile.html" class="w-9 h-9 rounded-full flex items-center justify-center font-bold" style="background:var(--accent-soft);color:var(--accent)">
            ${user.full_name.charAt(0).toUpperCase()}
          </a>
        </div>
      </div>
    `;
  }

  ORVO_THEME.apply(user.theme || ORVO_THEME.get());
  return user;
}
