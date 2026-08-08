// Official TradingView "Advanced Real-Time Chart" widget — free, no API key required.
// https://www.tradingview.com/widget/advanced-chart/
const ORVO_SYMBOLS = [
  { value: "BTCUSDT", tv: "BINANCE:BTCUSDT", label: "BTC/USDT (Crypto)" },
  { value: "ETHUSDT", tv: "BINANCE:ETHUSDT", label: "ETH/USDT (Crypto)" },
  { value: "BNBUSDT", tv: "BINANCE:BNBUSDT", label: "BNB/USDT (Crypto)" },
  { value: "SOLUSDT", tv: "BINANCE:SOLUSDT", label: "SOL/USDT (Crypto)" },
  { value: "EURUSD", tv: "FX:EURUSD", label: "EUR/USD (Forex)" },
  { value: "GBPUSD", tv: "FX:GBPUSD", label: "GBP/USD (Forex)" },
  { value: "XAUUSD", tv: "OANDA:XAUUSD", label: "XAU/USD (Gold)" },
  { value: "US30", tv: "TVC:DJI", label: "US30 (Index)" },
  { value: "NAS100", tv: "TVC:NDQ", label: "NAS100 (Index)" },
];

const TV_INTERVAL_MAP = { "15m": "15", "1h": "60", "4h": "240", "1d": "D" };

let tvWidget = null;

function renderTradingViewChart(symbolValue, timeframe) {
  const meta = ORVO_SYMBOLS.find((s) => s.value === symbolValue) || ORVO_SYMBOLS[0];
  const container = document.getElementById("tv_chart_container");
  container.innerHTML = "";

  const script = document.createElement("script");
  script.src = "https://s3.tradingview.com/tv.js";
  script.onload = () => {
    tvWidget = new TradingView.widget({
      autosize: true,
      symbol: meta.tv,
      interval: TV_INTERVAL_MAP[timeframe] || "60",
      timezone: "Etc/UTC",
      theme: document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark",
      style: "1",
      locale: "en",
      toolbar_bg: "#131822",
      enable_publishing: false,
      allow_symbol_change: false,
      hide_side_toolbar: false,
      container_id: "tv_chart_container",
    });
  };
  container.appendChild(script);
}

function populateSymbolSelect() {
  const select = document.getElementById("symbol-select");
  select.innerHTML = ORVO_SYMBOLS.map((s) => `<option value="${s.value}">${s.label}</option>`).join("");
}
