const BINANCE_SYMBOLS = new Set(["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]);

async function loadBrokerConnections() {
  const select = document.getElementById("broker-connection-select");
  try {
    const connections = await ORVO_API.get("/api/broker/connections");
    const connected = connections.filter((c) => c.status === "connected");
    if (!connected.length) {
      select.innerHTML = `<option value="">No broker connected</option>`;
      return null;
    }
    select.innerHTML = connected.map((c) => `<option value="${c.id}">${c.label} (${c.broker_type.toUpperCase()})</option>`).join("");
    return connected[0].id;
  } catch (err) {
    select.innerHTML = `<option value="">No broker connected</option>`;
    return null;
  }
}

async function loadAIAnalysis() {
  const symbol = document.getElementById("symbol-select").value;
  const timeframe = document.getElementById("timeframe-select").value;
  const panel = document.getElementById("ai-panel");

  if (!BINANCE_SYMBOLS.has(symbol)) {
    panel.innerHTML = `<p class="text-sm" style="color:var(--text-muted)">
      AI analysis currently runs on live crypto data (Binance). Forex/Gold/Index analysis
      needs a market-data provider with a license for that data (see README for how to add one) —
      it isn't faked here.
    </p>`;
    return;
  }

  panel.innerHTML = `<div class="skeleton h-24"></div>`;
  try {
    const r = await ORVO_API.get(`/api/ai/analyze?symbol=${symbol}&timeframe=${timeframe}`);
    const recColor = r.recommendation === "buy" ? "success" : r.recommendation === "sell" ? "danger" : "warning";
    panel.innerHTML = `
      <div class="flex items-center justify-between mb-3">
        <span class="badge badge-${recColor}">${r.recommendation.toUpperCase()}</span>
        <span class="text-sm font-semibold">${r.confidence}% confidence</span>
      </div>
      <div class="grid grid-cols-2 gap-2 text-xs mb-3" style="color:var(--text-secondary)">
        <div>Trend: <span style="color:var(--text-primary)">${r.trend}</span></div>
        <div>Structure: <span style="color:var(--text-primary)">${r.market_structure}</span></div>
        <div>BOS/CHOCH: <span style="color:var(--text-primary)">${r.bos_choch}</span></div>
        <div>Session: <span style="color:var(--text-primary)">${r.session}</span></div>
      </div>
      ${r.entry_price ? `
      <div class="grid grid-cols-3 gap-2 text-xs mb-3">
        <div class="stat-card p-2"><div style="color:var(--text-secondary)">Entry</div><div class="font-semibold">${r.entry_price}</div></div>
        <div class="stat-card p-2"><div style="color:var(--text-secondary)">SL</div><div class="font-semibold">${r.stop_loss}</div></div>
        <div class="stat-card p-2"><div style="color:var(--text-secondary)">TP</div><div class="font-semibold">${r.take_profit}</div></div>
      </div>` : ""}
      <p class="text-xs leading-relaxed" style="color:var(--text-secondary)">${r.explanation}</p>
    `;
    if (r.stop_loss) document.getElementById("order-sl").value = r.stop_loss;
    if (r.take_profit) document.getElementById("order-tp").value = r.take_profit;
  } catch (err) {
    panel.innerHTML = `<p class="text-sm" style="color:var(--danger)">${err.message}</p>`;
  }
}

async function loadOpenPositions() {
  const body = document.getElementById("open-positions-body");
  const empty = document.getElementById("open-positions-empty");
  try {
    const trades = await ORVO_API.get("/api/trading/trades?status_filter=open");
    if (!trades.length) {
      body.innerHTML = "";
      empty.classList.remove("hidden");
      return;
    }
    empty.classList.add("hidden");
    body.innerHTML = trades.map((t) => `
      <tr class="border-t" style="border-color:var(--border-color)">
        <td class="py-2 font-medium">${t.symbol}</td>
        <td class="py-2"><span class="badge ${t.side === 'buy' ? 'badge-success' : 'badge-danger'}">${t.side.toUpperCase()}</span></td>
        <td class="py-2">${t.lot_size}</td>
        <td class="py-2">${t.entry_price}</td>
        <td class="py-2">${t.stop_loss ?? "—"}</td>
        <td class="py-2">${t.take_profit ?? "—"}</td>
        <td class="py-2" style="color:var(--text-secondary)">${new Date(t.opened_at).toLocaleString()}</td>
        <td class="py-2"><button class="text-sm close-trade-btn" data-id="${t.id}" style="color:var(--danger)">Close</button></td>
      </tr>
    `).join("");
    document.querySelectorAll(".close-trade-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Close this position?")) return;
        try {
          await ORVO_API.post(`/api/trading/order/${btn.dataset.id}/close`);
          orvoShowToast("Position closed.", "success");
          loadOpenPositions();
        } catch (err) {
          orvoShowToast(err.message, "error");
        }
      });
    });
  } catch (err) {
    // non-fatal
  }
}

async function submitOrder(side) {
  const brokerSelect = document.getElementById("broker-connection-select");
  const brokerId = brokerSelect.value;
  if (!brokerId) {
    orvoShowToast("Connect a broker in Settings before trading.", "error");
    return;
  }
  const symbol = document.getElementById("symbol-select").value;
  if (!BINANCE_SYMBOLS.has(symbol)) {
    orvoShowToast("Live order routing in this build targets crypto pairs via Binance-priced symbols traded through your connected MT5 account. Confirm the symbol name matches your broker's listing.", "warning");
  }
  const lotSize = parseFloat(document.getElementById("lot-size").value);
  const sl = parseFloat(document.getElementById("order-sl").value);
  const tp = parseFloat(document.getElementById("order-tp").value);

  const oneClick = document.getElementById("one-click-toggle").checked;
  if (!oneClick) {
    if (!confirm(`Confirm ${side.toUpperCase()} ${lotSize || "auto"} lots of ${symbol}?`)) return;
  }

  try {
    await ORVO_API.post("/api/trading/order", {
      broker_connection_id: brokerId,
      symbol,
      side,
      lot_size: isNaN(lotSize) ? null : lotSize,
      stop_loss: isNaN(sl) ? null : sl,
      take_profit: isNaN(tp) ? null : tp,
    });
    orvoShowToast(`${side.toUpperCase()} order placed.`, "success");
    loadOpenPositions();
  } catch (err) {
    orvoShowToast(err.message, "error");
  }
}

(async () => {
  const user = await orvoInitAppShell();
  if (!user) return;

  populateSymbolSelect();
  renderTradingViewChart(document.getElementById("symbol-select").value, document.getElementById("timeframe-select").value);
  await loadBrokerConnections();
  await loadAIAnalysis();
  await loadOpenPositions();

  document.getElementById("symbol-select").addEventListener("change", () => {
    renderTradingViewChart(document.getElementById("symbol-select").value, document.getElementById("timeframe-select").value);
    loadAIAnalysis();
  });
  document.getElementById("timeframe-select").addEventListener("change", () => {
    renderTradingViewChart(document.getElementById("symbol-select").value, document.getElementById("timeframe-select").value);
    loadAIAnalysis();
  });
  document.getElementById("refresh-ai-btn").addEventListener("click", loadAIAnalysis);
  document.getElementById("buy-btn").addEventListener("click", () => submitOrder("buy"));
  document.getElementById("sell-btn").addEventListener("click", () => submitOrder("sell"));

  setInterval(loadOpenPositions, 15000);
})();
