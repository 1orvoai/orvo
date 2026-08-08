// ORVO API client — single source of truth for talking to the FastAPI backend.
const ORVO_API = {
  base: "", // same-origin

  getToken() {
    return localStorage.getItem("orvo_token");
  },
  setToken(token) {
    localStorage.setItem("orvo_token", token);
  },
  clearToken() {
    localStorage.removeItem("orvo_token");
  },
  isAuthenticated() {
    return !!this.getToken();
  },

  async request(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const resp = await fetch(this.base + path, { ...options, headers });

    if (resp.status === 401) {
      this.clearToken();
      if (!location.pathname.includes("login.html") && !location.pathname.includes("signup.html") && location.pathname !== "/" && !location.pathname.includes("index.html")) {
        window.location.href = "/login.html";
      }
      throw new Error("Not authenticated");
    }

    let data = null;
    try {
      data = await resp.json();
    } catch (e) {
      data = null;
    }

    if (!resp.ok) {
      const message = (data && data.detail) ? data.detail : `Request failed (${resp.status})`;
      throw new Error(typeof message === "string" ? message : JSON.stringify(message));
    }
    return data;
  },

  get(path) {
    return this.request(path, { method: "GET" });
  },
  post(path, body) {
    return this.request(path, { method: "POST", body: JSON.stringify(body || {}) });
  },
  put(path, body) {
    return this.request(path, { method: "PUT", body: JSON.stringify(body || {}) });
  },
  del(path) {
    return this.request(path, { method: "DELETE" });
  },
};

function orvoShowToast(message, type = "info") {
  const containerId = "orvo-toast-container";
  let container = document.getElementById(containerId);
  if (!container) {
    container = document.createElement("div");
    container.id = containerId;
    container.style.cssText = "position:fixed;top:20px;right:20px;z-index:10000;display:flex;flex-direction:column;gap:10px;";
    document.body.appendChild(container);
  }
  const colors = { info: "#3b82f6", success: "#22c55e", error: "#ef4444", warning: "#f59e0b" };
  const toast = document.createElement("div");
  toast.textContent = message;
  toast.style.cssText = `background:var(--bg-card,#131822);border-left:4px solid ${colors[type] || colors.info};color:var(--text-primary,#e6e9ef);padding:12px 18px;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,0.3);min-width:260px;max-width:360px;font-size:14px;animation:orvo-fade-in 0.25s ease;`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = "opacity 0.3s ease";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function orvoFormatCurrency(value, currency = "USD") {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(value);
}

function orvoFormatPercent(value) {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(1)}%`;
}
