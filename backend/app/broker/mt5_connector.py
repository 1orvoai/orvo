import os
from typing import Dict, List, Optional

import requests


MT5_BRIDGE_URL = os.getenv(
    "MT5_BRIDGE_URL",
    "http://194.146.38.31:8000"
)


TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w",
}


def _get(endpoint: str, params: Optional[Dict] = None) -> Dict:
    try:
        response = requests.get(
            f"{MT5_BRIDGE_URL}{endpoint}",
            params=params,
            timeout=15
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"MT5 bridge connection failed: {str(e)}"
        }


def _post(endpoint: str, data: Dict) -> Dict:
    try:
        response = requests.post(
            f"{MT5_BRIDGE_URL}{endpoint}",
            json=data,
            timeout=15
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"MT5 bridge connection failed: {str(e)}"
        }


def is_supported() -> bool:
    return True


def connect() -> Dict:
    result = _get("/mt5/status")

    if result.get("connected") is True:
        return {
            "success": True,
            **result,
        }

    return {
        "success": False,
        **result,
    }


def status() -> Dict:
    return _get("/mt5/status")


def get_klines(
    symbol: str,
    interval: str = "1h",
    limit: int = 200
) -> List[Dict]:
    """
    Get OHLCV candles from MetaTrader 5 through the ORVO MT5 bridge.

    Returns candles in the same structure expected by ORVO's
    technical-analysis engine.
    """

    interval = interval.lower()

    if interval not in TIMEFRAME_MAP:
        raise ValueError(
            f"Unsupported timeframe: {interval}"
        )

    result = _get(
        "/mt5/candles",
        params={
            "symbol": symbol.upper(),
            "timeframe": TIMEFRAME_MAP[interval],
            "limit": limit,
        }
    )

    if result.get("success") is not True:
        raise RuntimeError(
            result.get(
                "error",
                "Failed to retrieve MT5 candles"
            )
        )

    return result.get("candles", [])


def place_order(
    symbol: str,
    lot_size: float,
    side: str,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
) -> Dict:

    return _post(
        "/mt5/order",
        {
            "symbol": symbol,
            "volume": float(lot_size),
            "side": side,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }
    )


def close_order(
    ticket: int,
    symbol: str,
    side: str,
    lot_size: float
) -> Dict:

    return _post(
        "/mt5/close",
        {
            "ticket": int(ticket),
            "symbol": symbol,
            "side": side,
            "volume": float(lot_size),
        }
    )


def modify_order(
    ticket: int,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None
) -> Dict:

    return _post(
        "/mt5/modify",
        {
            "ticket": int(ticket),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }
    )


def shutdown() -> Dict:
    return {"success": True}


def get_account_snapshot() -> Dict:
    result = _get("/mt5/status")

    return {
        "balance": float(result.get("balance", 0)),
        "equity": float(result.get("equity", 0)),
        "margin": float(result.get("margin", 0)),
        "free_margin": float(result.get("free_margin", 0)),
        "currency": result.get("currency", "USD"),
    }
