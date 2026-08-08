async function loadMT5Support() {
  try {
    const support = await ORVO_API.get("/api/broker/mt5/status");
    const note = document.getElementById("mt5-support-note");
    if (support.supported) {
      note.textContent = "MT5 integration is available on this server. Enter your account credentials below.";
      note.style.color = "var(--success)";
    } else {
      note.textContent = `MT5 not available on this server: ${support.reason}`;
      note.style.color = "var(--warning)";
    }
  } catch (err) {
    // non-fatal
  }
}

async function loadBrokerConnections() {
  const list = document.getElementById("broker-connections-list");
  try {
    const connections = await ORVO_API.get("/api/broker/connections");
    if (!connections.length) {
      list.innerHTML = `<p class="text-sm" style="color:var(--text-muted)">No broker accounts connected yet.</p>`;
      return;
    }
    list.innerHTML = connections.map((c) => `
      <div class="flex items-center justify-between stat-card">
        <div>
          <div class="font-medium">${c.label} <span class="badge ${c.status === 'connected' ? 'badge-success' : 'badge-danger'} ml-2">${c.status}</span></div>
          <div class="text-xs mt-1" style="color:var(--text-secondary)">${c.broker_type.toUpperCase()} · ${c.account_login || ''} @ ${c.server || ''}</div>
          ${c.last_error ? `<div class="text-xs mt-1" style="color:var(--danger)">${c.last_error}</div>` : ''}
        </div>
        <button class="text-sm remove-conn-btn" data-id="${c.id}" style="color:var(--danger)">Remove</button>
      </div>
    `).join("");
    document.querySelectorAll(".remove-conn-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Remove this broker connection?")) return;
        try {
          await ORVO_API.del(`/api/broker/connections/${btn.dataset.id}`);
          orvoShowToast("Connection removed.", "success");
          loadBrokerConnections();
        } catch (err) {
          orvoShowToast(err.message, "error");
        }
      });
    });
  } catch (err) {
    list.innerHTML = `<p class="text-sm" style="color:var(--danger)">${err.message}</p>`;
  }
}

async function loadRiskSettings() {
  try {
    const risk = await ORVO_API.get("/api/risk/settings");
    Object.entries(risk).forEach(([key, value]) => {
      const el = document.getElementById(key);
      if (!el) return;
      if (el.type === "checkbox") el.checked = value;
      else el.value = value;
    });
  } catch (err) {
    orvoShowToast("Could not load risk settings: " + err.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("mt5-connect-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("mt5-connect-btn");
    btn.disabled = true;
    btn.textContent = "Connecting...";
    try {
      await ORVO_API.post("/api/broker/mt5/connect", {
        login: document.getElementById("mt5-login").value.trim(),
        password: document.getElementById("mt5-password").value,
        server: document.getElementById("mt5-server").value.trim(),
        label: document.getElementById("mt5-label").value.trim() || "MT5 Account",
      });
      orvoShowToast("MT5 account connected!", "success");
      loadBrokerConnections();
    } catch (err) {
      orvoShowToast(err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Connect MT5 Account";
    }
  });

  document.getElementById("risk-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fields = [
      "risk_percent_per_trade", "daily_loss_limit_percent", "daily_profit_target_percent",
      "max_drawdown_percent", "max_open_trades", "default_stop_loss_pips", "default_take_profit_pips",
      "trailing_stop_pips", "breakeven_trigger_pips",
    ];
    const checkboxFields = ["use_trailing_stop", "use_breakeven", "auto_close_on_daily_loss", "auto_trading_enabled"];
    const payload = {};
    fields.forEach((f) => {
      const val = parseFloat(document.getElementById(f).value);
      if (!isNaN(val)) payload[f] = val;
    });
    checkboxFields.forEach((f) => {
      payload[f] = document.getElementById(f).checked;
    });
    try {
      await ORVO_API.put("/api/risk/settings", payload);
      orvoShowToast("Risk settings saved.", "success");
    } catch (err) {
      orvoShowToast(err.message, "error");
    }
  });

  document.getElementById("lot-calc-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const res = await ORVO_API.post("/api/trading/lot-calculator", {
        account_balance: parseFloat(document.getElementById("calc-balance").value),
        risk_percent: parseFloat(document.getElementById("calc-risk").value),
        stop_loss_pips: parseFloat(document.getElementById("calc-sl").value),
      });
      document.getElementById("lot-calc-result").innerHTML = `
        Recommended lot size: <strong>${res.lot_size}</strong> ·
        Risk amount: <strong>${orvoFormatCurrency(res.risk_amount)}</strong>
        <div class="text-xs mt-1" style="color:var(--text-muted)">${res.formula}</div>
      `;
    } catch (err) {
      orvoShowToast(err.message, "error");
    }
  });

  document.getElementById("theme-dark-btn")?.addEventListener("click", () => ORVO_THEME.apply("dark"));
  document.getElementById("theme-light-btn")?.addEventListener("click", () => ORVO_THEME.apply("light"));
});

async function loadNewsStatus() {
  try {
    const res = await ORVO_API.get("/api/news/economic-calendar");
    const el = document.getElementById("news-status");
    if (res.configured) {
      el.innerHTML = `<span class="badge badge-success">Configured</span> ${res.high_impact_events.length} high-impact events in the next 7 days.`;
    } else {
      el.innerHTML = `<span class="badge badge-warning">Not configured</span> ${res.message}`;
    }
  } catch (err) {
    // non-fatal
  }
}

(async () => {
  const user = await orvoInitAppShell();
  if (!user) return;
  await loadMT5Support();
  await loadBrokerConnections();
  await loadRiskSettings();
  await loadNewsStatus();
})();
