"""
Real market data client using Binance's public REST API.
No API key is required for public market data endpoints.
Docs: https://binance-docs.github.io/apidocs/spot/en/
"""
from typing import List, Dict
import httpx
from ..config import settings

INTERVAL_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w",
}


async def get_klines(symbol: str, interval: str = "1h", limit: int = 200) -> List[Dict]:
    """Fetch OHLCV candles for a symbol. Returns list of dicts oldest->newest."""
    if interval not in INTERVAL_MAP:
        raise ValueError(f"Unsupported interval: {interval}")
    url = f"{settings.BINANCE_REST_URL}/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": INTERVAL_MAP[interval], "limit": limit}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        raw = resp.json()

    candles = []
    for row in raw:
        candles.append({
            "open_time": row[0],
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
            "close_time": row[6],
        })
    return candles


async def get_ticker(symbol: str) -> Dict:
    url = f"{settings.BINANCE_REST_URL}/api/v3/ticker/24hr"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params={"symbol": symbol.upper()})
        resp.raise_for_status()
        data = resp.json()
    return {
        "symbol": data["symbol"],
        "price": float(data["lastPrice"]),
        "change_percent": float(data["priceChangePercent"]),
        "high_24h": float(data["highPrice"]),
        "low_24h": float(data["lowPrice"]),
        "volume_24h": float(data["volume"]),
    }


async def get_multiple_tickers(symbols: List[str]) -> List[Dict]:
    results = []
    async with httpx.AsyncClient(timeout=10) as client:
        for sym in symbols:
            try:
                resp = await client.get(
                    f"{settings.BINANCE_REST_URL}/api/v3/ticker/24hr",
                    params={"symbol": sym.upper()},
                )
                resp.raise_for_status()
                data = resp.json()
                results.append({
                    "symbol": data["symbol"],
                    "price": float(data["lastPrice"]),
                    "change_percent": float(data["priceChangePercent"]),
                })
            except Exception as e:
                results.append({"symbol": sym.upper(), "error": str(e)})
    return results


def binance_ws_stream_url(symbols: List[str], interval: str = "1m") -> str:
    """Combined kline stream URL for live candle updates."""
    streams = "/".join(f"{s.lower()}@kline_{interval}" for s in symbols)
    return f"{settings.BINANCE_WS_URL}/stream?streams={streams}"
