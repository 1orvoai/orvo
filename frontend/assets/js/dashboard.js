let equityChart = null;

async function loadDashboard() {
  try {
    const summary = await ORVO_API.get("/api/dashboard/summary");

    document.getElementById("stat-balance").textContent = orvoFormatCurrency(summary.balance, summary.currency);
    document.getElementById("stat-equity").textContent = orvoFormatCurrency(summary.equity, summary.currency);
    document.getElementById("stat-margin").textContent = orvoFormatCurrency(summary.margin, summary.currency);
    document.getElementById("stat-free-margin").textContent = orvoFormatCurrency(summary.free_margin, summary.currency);

    const dailyPlEl = document.getElementById("stat-daily-pl");
    dailyPlEl.textContent = orvoFormatCurrency(summary.daily_pl, summary.currency);
    dailyPlEl.style.color = summary.daily_pl >= 0 ? "var(--success)" : "var(--danger)";

    const totalProfitEl = document.getElementById("stat-total-profit");
    totalProfitEl.textContent = orvoFormatCurrency(summary.total_profit, summary.currency);
    totalProfitEl.style.color = summary.total_profit >= 0 ? "var(--success)" : "var(--danger)";

    document.getElementById("stat-win-rate").textContent = orvoFormatPercent(summary.win_rate);
    document.getElementById("stat-risk-score").textContent = `${summary.risk_score} / 100`;
    document.getElementById("stat-open-trades").textContent = summary.open_trades;
    document.getElementById("stat-trades-today").textContent = summary.trades_today;
    document.getElementById("stat-auto-trading").textContent = summary.auto_trading_enabled ? "Enabled" : "Disabled";

    ["stat-balance","stat-equity","stat-margin","stat-free-margin","stat-win-rate","stat-risk-score","stat-open-trades","stat-trades-today","stat-auto-trading"].forEach(id => {
      document.getElementById(id).classList.remove("skeleton","h-8");
    });
    dailyPlEl.classList.remove("skeleton","h-8");
    totalProfitEl.classList.remove("skeleton","h-8");

    const brokerBadge = document.getElementById("broker-badge");
    if (summary.broker_connected) {
      brokerBadge.textContent = "Broker connected";
      brokerBadge.className = "badge badge-success";
    } else {
      brokerBadge.textContent = "No broker connected — go to Settings";
      brokerBadge.className = "badge badge-warning";
    }
  } catch (err) {
    orvoShowToast("Could not load dashboard summary: " + err.message, "error");
  }

  try {
    const aiResult = await ORVO_API.get("/api/ai/analyze?symbol=BTCUSDT&timeframe=1h");
    const el = document.getElementById("stat-ai-confidence");
    el.textContent = `${aiResult.confidence}%`;
    el.classList.remove("skeleton", "h-8");
  } catch (err) {
    document.getElementById("stat-ai-confidence").textContent = "N/A";
  }

  try {
    const curve = await ORVO_API.get("/api/dashboard/equity-curve");
    renderEquityChart(curve.points);
  } catch (err) {
    // non-fatal
  }

  try {
    const trades = await ORVO_API.get("/api/trading/trades");
    renderTradeHistory(trades);
  } catch (err) {
    // non-fatal
  }
}

function renderEquityChart(points) {
  const ctx = document.getElementById("equity-chart");
  const labels = points.map((p, i) => p.date ? new Date(p.date).toLocaleDateString() : `#${i + 1}`);
  const data = points.map((p) => p.cumulative_pl);

  if (equityChart) equityChart.destroy();
  equityChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels.length ? labels : ["No data yet"],
      datasets: [{
        label: "Cumulative P/L",
        data: data.length ? data : [0],
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59,130,246,0.12)",
        fill: true,
        tension: 0.3,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#8b94a7" } },
        y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#8b94a7" } },
      },
    },
  });
}

function renderTradeHistory(trades) {
  const body = document.getElementById("trade-history-body");
  const empty = document.getElementById("trade-history-empty");
  if (!trades.length) {
    empty.classList.remove("hidden");
    return;
  }
  body.innerHTML = trades.map((t) => `
    <tr class="border-t" style="border-color:var(--border-color)">
      <td class="py-2 font-medium">${t.symbol}</td>
      <td class="py-2"><span class="badge ${t.side === 'buy' ? 'badge-success' : 'badge-danger'}">${t.side.toUpperCase()}</span></td>
      <td class="py-2">${t.lot_size}</td>
      <td class="py-2">${t.entry_price}</td>
      <td class="py-2">${t.exit_price ?? "—"}</td>
      <td class="py-2" style="color:${t.profit >= 0 ? 'var(--success)' : 'var(--danger)'}">${orvoFormatCurrency(t.profit)}</td>
      <td class="py-2"><span class="badge ${t.status === 'open' ? 'badge-neutral' : 'badge-warning'}">${t.status}</span></td>
      <td class="py-2" style="color:var(--text-secondary)">${new Date(t.opened_at).toLocaleString()}</td>
    </tr>
  `).join("");
}

function connectWatchlistWS() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${proto}//${location.host}/ws/dashboard`);
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "watchlist") {
      const container = document.getElementById("watchlist");
      container.innerHTML = msg.data.map((t) => {
        if (t.error) return "";
        const up = t.change_percent >= 0;
        return `
          <div class="flex items-center justify-between text-sm">
            <span class="font-medium">${t.symbol}</span>
            <span class="flex items-center gap-2">
              <span>${orvoFormatCurrency(t.price)}</span>
              <span style="color:${up ? 'var(--success)' : 'var(--danger)'}">${up ? '▲' : '▼'} ${Math.abs(t.change_percent).toFixed(2)}%</span>
            </span>
          </div>`;
      }).join("");
    }
  };
  ws.onerror = () => {};
  ws.onclose = () => setTimeout(connectWatchlistWS, 5000);
}

(async () => {
  const user = await orvoInitAppShell();
  if (!user) return;
  await loadDashboard();
  connectWatchlistWS();
  setInterval(loadDashboard, 30000);
})();
