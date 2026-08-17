const MT5_SYMBOLS = new Set(["BTCUSDTm","GBPUSDm","EURUSDm","XAUUSDm"]);

async function loadBrokerConnections() {
  const select = document.getElementById("broker-connection-select");
  try {
    const connections = await ORVO_API.get("/api/broker/connections");
    const connected = connections.filter(c => c.status === "connected");

    if (!connected.length) {
      select.innerHTML = <option value="">No broker connected</option>;
      return null;
    }

    select.innerHTML = connected.map(c =>
      <option value="${c.id}">${c.label} (${c.broker_type.toUpperCase()})</option>
    ).join("");

    return connected[0].id;
  } catch (err) {
    select.innerHTML = <option value="">No broker connected</option>;
    return null;
  }
}

async function loadAIAnalysis() {
  const symbol = document.getElementById("symbol-select").value;
  const timeframe = document.getElementById("timeframe-select").value;
  const panel = document.getElementById("ai-panel");

  panel.innerHTML = <div class="skeleton h-24"></div>;

  try {
    const r = await ORVO_API.get(
      /api/ai/analyze?symbol=${symbol}&timeframe=${timeframe}
    );

    const color = r.recommendation === "buy" ? "success" :
                  r.recommendation === "sell" ? "danger" : "warning";

    panel.innerHTML = 
      <div class="flex justify-between mb-3">
        <span class="badge badge-${color}">${r.recommendation.toUpperCase()}</span>
        <span class="text-sm font-semibold">${r.confidence}% confidence</span>
      </div>
      <div class="grid grid-cols-2 gap-2 text-xs mb-3"
           style="color:var(--text-secondary)">
        <div>Trend: ${r.trend}</div>
        <div>Structure: ${r.market_structure}</div>
        <div>BOS/CHOCH: ${r.bos_choch}</div>
        <div>Session: ${r.session}</div>
      </div>
      ${r.entry_price ? 
        <div class="grid grid-cols-3 gap-2 text-xs mb-3">
          <div class="stat-card p-2">Entry<br><b>${r.entry_price}</b></div>
          <div class="stat-card p-2">SL<br><b>${r.stop_loss}</b></div>
          <div class="stat-card p-2">TP<br><b>${r.take_profit}</b></div>
        </div> : ""}
      <p class="text-xs" style="color:var(--text-secondary)">${r.explanation}</p>;

    if (r.stop_loss) document.getElementById("order-sl").value = r.stop_loss;
    if (r.take_profit) document.getElementById("order-tp").value = r.take_profit;

  } catch (err) {
    panel.innerHTML = <p class="text-sm" style="color:var(--danger)">${err.message}</p>;
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
    body.innerHTML = trades.map(t => 
      <tr class="border-t">
        <td class="py-2">${t.symbol}</td>
        <td class="py-2"><span class="badge ${t.side === "buy" ? "badge-success" : "badge-danger"}">${t.side.toUpperCase()}</span></td>
        <td class="py-2">${t.lot_size}</td>
        <td class="py-2">${t.entry_price}</td>
        <td class="py-2">${t.stop_loss ?? "—"}</td>
        <td class="py-2">${t.take_profit ?? "—"}</td>
        <td class="py-2">${new Date(t.opened_at).toLocaleString()}</td>
        <td class="py-2"><button class="close-trade-btn" data-id="${t.id}">Close</button></td>
      </tr>).join("");

    document.querySelectorAll(".close-trade-btn").forEach(btn => {
      btn.onclick = async () => {
        if (!confirm("Close this position?")) return;
        try {
          await ORVO_API.post(/api/trading/order/${btn.dataset.id}/close);
          orvoShowToast("Position closed.", "success");
          loadOpenPositions();
        } catch (err) {
          orvoShowToast(err.message, "error");
        }
      };
    });
  } catch (err) {}
}

async function submitOrder(side) {
  const brokerId = document.getElementById("broker-connection-select").value;
  if (!brokerId) return orvoShowToast("Connect a broker in Settings before trading.", "error");

  const symbol = document.getElementById("symbol-select").value;
  const lotSize = parseFloat(document.getElementById("lot-size").value);
  const sl = parseFloat(document.getElementById("order-sl").value);
  const tp = parseFloat(document.getElementById("order-tp").value);

  if (!document.getElementById("one-click-toggle").checked &&
      !confirm(Confirm ${side.toUpperCase()} ${lotSize || "auto"} lots of ${symbol}?)) return;

  try {
    await ORVO_API.post("/api/trading/order", {
      broker_connection_id: brokerId,
      symbol, side,
      lot_size: isNaN(lotSize) ? null : lotSize,
      stop_loss: isNaN(sl) ? null : sl,
      take_profit: isNaN(tp) ? null : tp
    });
    orvoShowToast(${side.toUpperCase()} order placed., "success");
    loadOpenPositions();
  } catch (err) {
    orvoShowToast(err.message, "error");
  }
}

(async () => {
  const user = await orvoInitAppShell();
  if (!user) return;

  populateSymbolSelect();

  const symbol = document.getElementById("symbol-select");
  const timeframe = document.getElementById("timeframe-select");

  renderTradingViewChart(symbol.value, timeframe.value);
  await loadBrokerConnections();
  await loadAIAnalysis();
  await loadOpenPositions();

  symbol.onchange = () => {
    renderTradingViewChart(symbol.value, timeframe.value);
    loadAIAnalysis();
  };

  timeframe.onchange = () => {
    renderTradingViewChart(symbol.value, timeframe.value);
    loadAIAnalysis();
  };

  document.getElementById("refresh-ai-btn").onclick = loadAIAnalysis;
  document.getElementById("buy-btn").onclick = () => submitOrder("buy");
  document.getElementById("sell-btn").onclick = () => submitOrder("sell");

  setInterval(loadOpenPositions, 15000);
})();
